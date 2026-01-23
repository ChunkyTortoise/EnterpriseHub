import json
from datetime import datetime
from typing import Dict, List, Optional
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from modules.db import SessionLocal, init_db, Property, Lead, Interaction

# Ensure DB is initialized
init_db()

class InventoryManager:
    def __init__(self):
        """Initialize the manager."""
        # Database connection is handled via SessionLocal in methods
        pass

    def get_db(self) -> Session:
        """Helper to get a database session."""
        return SessionLocal()

    # --- Core Logic: Ingestion ---
    def ingest_listing(self, listing: Dict, use_vision: bool = False):
        """
        Takes a raw JSON listing and saves it to the DB with AI enrichment.
        """
        # 1. AI Enrichment (Text-based Tagging)
        if 'tags' in listing:
            tags = listing['tags'] if isinstance(listing['tags'], list) else json.loads(listing['tags'])
        else:
            tags_dict = self._generate_ai_tags(listing.get('description', ''))
            tags = [k for k, v in tags_dict.items() if v]
        
        # 2. Vision Enrichment (Optional)
        image_url = listing.get('image_url')
        if use_vision and image_url:
            vision_tags = self._generate_vision_tags(image_url)
            tags.extend(vision_tags)
            tags = list(set(tags)) # Remove duplicates
        
        # 3. Upsert Logic
        with self.get_db() as db:
            prop_id = listing['id']
            existing_prop = db.execute(select(Property).where(Property.id == prop_id)).scalar_one_or_none()
            
            # Map dictionary to Model
            prop_data = {
                "id": prop_id,
                "address": listing['address']['street'] if isinstance(listing['address'], dict) else listing['address'],
                "city": listing['address']['city'] if isinstance(listing['address'], dict) else listing.get('city', 'Unknown'),
                "price": listing['price'],
                "beds": listing.get('bedrooms', listing.get('beds', 0)),
                "baths": listing.get('bathrooms', listing.get('baths', 0)),
                "sqft": listing['sqft'],
                "description": listing.get('description', ''),
                "image_url": image_url,
                "tags": tags,
                "list_date": datetime.now()
            }

            if existing_prop:
                # Update fields
                for key, value in prop_data.items():
                    setattr(existing_prop, key, value)
                print(f"✅ Updated: {prop_data['address']}")
            else:
                # Insert new
                new_prop = Property(**prop_data)
                db.add(new_prop)
                print(f"✅ Ingested: {prop_data['address']}")
            
            db.commit()

    def _generate_vision_tags(self, image_url: str) -> List[str]:
        """
        Uses Claude 3.5 Sonnet to analyze the property photo.
        """
        try:
            from ghl_real_estate_ai.services.ai_vision_tagger import VisionTagger
            tagger = VisionTagger()
            return tagger.analyze_property_image(image_url)
        except Exception as e:
            print(f"⚠️ Vision Tagging Failed: {e}")
            return []

    def ingest_lead(self, lead: Dict):
        """
        Ingests a lead to test the matching logic.
        """
        pref = lead.get('preferences', {})
        must_haves = pref.get('must_haves', [])
        
        with self.get_db() as db:
            lead_id = lead['id']
            existing_lead = db.execute(select(Lead).where(Lead.id == lead_id)).scalar_one_or_none()
            
            lead_data = {
                "id": lead_id,
                "name": lead['name'],
                "phone": lead.get('phone', ''),
                "max_budget": pref.get('budget', 500000),
                "min_beds": pref.get('bedrooms', 2),
                "preferred_neighborhood": pref.get('neighborhood', 'N/A'),
                "must_haves": must_haves
            }
            
            if existing_lead:
                for key, value in lead_data.items():
                    setattr(existing_lead, key, value)
            else:
                new_lead = Lead(**lead_data)
                db.add(new_lead)
            
            db.commit()
            print(f"👤 Saved Lead: {lead['name']}")

    def get_lead(self, lead_id: str) -> Optional[Dict]:
        """Retrieves a lead by ID."""
        with self.get_db() as db:
            lead = db.execute(select(Lead).where(Lead.id == lead_id)).scalar_one_or_none()
            if lead:
                return {
                    "id": lead.id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "max_budget": lead.max_budget,
                    "min_beds": lead.min_beds,
                    "preferred_neighborhood": lead.preferred_neighborhood,
                    "must_haves": lead.must_haves
                }
            return None

    # --- Core Logic: Intelligence ---
    def _generate_ai_tags(self, description: str) -> Dict[str, bool]:
        """
        Scans description for features using Google Gemini (preferred) or Anthropic Claude.
        """
        # Fallback keyword logic
        desc = description.lower()
        keyword_tags = {
            "has_pool": any(x in desc for x in ["pool", "spa", "swim"]),
            "modern_kitchen": any(x in desc for x in ["island", "granite", "quartz", "stainless"]),
            "large_lot": any(x in desc for x in ["acre", "lot", "yard"])
        }

        # Try Gemini First (Cost Efficient)
        google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                model = genai.GenerativeModel('gemini-1.5-flash') 
                
                prompt = f"""
                Extract real estate features from this description: "{description}"
                Return ONLY a valid JSON object with boolean values for: has_pool, modern_kitchen, large_lot.
                Example: {{'has_pool': true, 'modern_kitchen': false, 'large_lot': true}}
                Do not include Markdown formatting like ```json ... ```.
                """
                
                response = model.generate_content(prompt)
                text = response.text.strip()
                # Cleanup potential markdown
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("\n", 1)[0]
                    
                return json.loads(text)
            except Exception as e:
                print(f"⚠️ Gemini Tagging Failed: {e}. Trying Claude...")

        # Fallback to Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return keyword_tags

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                temperature=0,
                system="Extract real estate features from the description. Return ONLY a JSON object with boolean values for: has_pool, modern_kitchen, large_lot. Do not include any other text.",
                messages=[
                    {"role": "user", "content": f"Description: {description}"}
                ]
            )
            
            content = message.content[0].text
            import re
            json_match = re.search(r'\{{.*\}}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return keyword_tags
            
        except Exception as e:
            print(f"⚠️ Claude Tagging Failed: {e}. Using keywords.")
            return keyword_tags

    def calculate_match_score(self, lead: Lead, property: Property) -> int:
        """
        The Core Algorithm: Returns a 0-100 Score.
        Updated for SQLAlchemy Objects.
        """
        score = 0
        
        # 1. Price Logic (40 Points)
        if not lead.max_budget or not property.price:
            return 50 # Neutral if no data
            
        price_ratio = property.price / lead.max_budget
        if price_ratio > 1.10: # Hard Cap (10% wiggle room)
            return 0 
        
        if 0.8 <= price_ratio <= 1.0:
            score += 40
        elif price_ratio < 0.8:
            score += 30 # Under budget is good
        else:
            score += 20 # Slightly over budget

        # 2. Bedroom Logic (30 Points)
        if not property.beds or not lead.min_beds:
            score += 15 # Neutral
        else:
            bed_diff = property.beds - lead.min_beds
            if bed_diff == 0:
                score += 30
            elif bed_diff > 0:
                score += 35 # Bonus!
            elif bed_diff == -1:
                score += 10 # 1 bed short
            else:
                return 0 # Deal breaker

        # 3. Features/Tags Logic (30 Points)
        lead_tags = set(lead.must_haves or [])
        prop_tags = set(property.tags or [])
        
        if not lead_tags:
            score += 30
        else:
            matches = lead_tags.intersection(prop_tags)
            match_percentage = len(matches) / len(lead_tags)
            score += int(30 * match_percentage)

        return min(score, 100)

    def get_property(self, property_id: str) -> Optional[Dict]:
        """
        Retrieves a single property by its ID.
        """
        with self.get_db() as db:
            prop = db.execute(select(Property).where(Property.id == property_id)).scalar_one_or_none()
            if not prop:
                return None
                
            return {
                "id": prop.id,
                "address": prop.address,
                "city": prop.city,
                "price": prop.price,
                "beds": prop.beds,
                "baths": prop.baths,
                "sqft": prop.sqft,
                "description": prop.description,
                "tags": prop.tags
            }

    def get_smart_deck(self, lead_id: str) -> List[Dict]:
        """
        Generates a personalized deck of properties for a specific lead.
        """
        with self.get_db() as db:
            lead = db.execute(select(Lead).where(Lead.id == lead_id)).scalar_one_or_none()
            if not lead:
                return []

            # Get all active properties
            properties = db.execute(select(Property).where(Property.status == 'Active')).scalars().all()
            
            deck = []
            for prop in properties:
                score = self.calculate_match_score(lead, prop)
                if score >= 40:
                    deck.append({
                        "id": prop.id,
                        "address": prop.address,
                        "city": prop.city,
                        "price": prop.price,
                        "beds": prop.beds,
                        "baths": prop.baths,
                        "sqft": prop.sqft,
                        "description": prop.description,
                        "tags": prop.tags,
                        "match_score": score
                    })
            
            return sorted(deck, key=lambda x: x['match_score'], reverse=True)

    def log_interaction(self, lead_id: str, property_id: str, action: str, feedback: Optional[Dict] = None, time_on_card: Optional[float] = None):
        """
        Logs a swipe interaction (like/pass) to the database.
        """
        with self.get_db() as db:
            interaction = Interaction(
                lead_id=lead_id,
                property_id=property_id,
                action=action,
                feedback=feedback,
                time_on_card=time_on_card
            )
            db.add(interaction)
            db.commit()
            print(f"Logged {action} from {lead_id} on {property_id}")

    # --- Runner ---
if __name__ == "__main__":
    manager = InventoryManager()

    # 1. Load Mock Leads
    print("\n--- Loading Leads ---")
    mock_leads = [
        {
          "id": "lead_001", "name": "Sarah Johnson",
          "preferences": { "budget": 1350000, "bedrooms": 4, "must_haves": ["has_pool", "modern_kitchen"] }
        },
        {
          "id": "lead_002", "name": "Mike Chen",
          "preferences": { "budget": 700000, "bedrooms": 2, "must_haves": ["modern_kitchen"] }
        }
    ]
    for l in mock_leads:
        manager.ingest_lead(l)

    # 2. Ingest Property
    print("\n--- Ingesting Listing ---")
    prop = {
        "id": "rc_001",
        "price": 1250000, "bedrooms": 4, "bathrooms": 3, "sqft": 3200,
        "address": { "street": "12345 Hilltop Dr", "city": "Rancho Cucamonga" },
        "description": "Stunning hillside home with pool and gourmet kitchen."
    }
    manager.ingest_listing(prop)
    
    # 3. Test Weighted Match
    # Note: find_weighted_matches was not implemented in the previous version, 
    # but get_smart_deck does the job.
    print(f"\n--- Smart Deck for {mock_leads[0]['name']} ---")
    deck = manager.get_smart_deck("lead_001")
    for card in deck:
        print(f"🎯 {card['address']}: {card['match_score']}% match")
