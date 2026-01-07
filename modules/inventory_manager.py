import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

# --- Configuration ---
# Use a local database file
DEFAULT_DB = "real_estate_engine.db"

def get_db_path():
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return os.getenv("DB_PATH", DEFAULT_DB)

class InventoryManager:
    def __init__(self, db_path: str = None):
        """Initialize the manager and connect to the database."""
        self.db_path = db_path or get_db_path()
        
        # Ensure directory exists if it's in a subfolder
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self._init_db()

    def _init_db(self):
        """Creates the necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Properties Table (Updated with 'tags')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                address TEXT,
                city TEXT,
                price INTEGER,
                beds INTEGER,
                baths REAL,
                sqft INTEGER,
                description TEXT,
                image_url TEXT,
                status TEXT DEFAULT 'Active',
                list_date DATETIME,
                tags TEXT -- JSON String: ["pool", "modern_kitchen", "large_lot"]
            )
        """)
        
        # 2. Leads Table (Updated with 'must_haves')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                max_budget INTEGER,
                min_beds INTEGER,
                preferred_neighborhood TEXT,
                must_haves TEXT -- JSON String: ["pool", "modern_kitchen"]
            )
        """)
        
        conn.commit()
        conn.close()

    # --- Core Logic: Ingestion ---
    def ingest_listing(self, listing: Dict, use_vision: bool = False):
        """
        Takes a raw JSON listing and saves it to the DB with AI enrichment.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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
            # Remove duplicates
            tags = list(set(tags))
        
        # 3. Upsert Logic (Insert or Update)
        try:
            cursor.execute("""
                INSERT INTO properties (
                    id, address, city, price, beds, baths, sqft, description, 
                    image_url, tags, list_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    price=excluded.price,
                    status=excluded.status,
                    tags=excluded.tags,
                    image_url=excluded.image_url
            """, (
                listing['id'], 
                listing['address']['street'] if isinstance(listing['address'], dict) else listing['address'], 
                listing['address']['city'] if isinstance(listing['address'], dict) else listing.get('city', 'Unknown'), 
                listing['price'], 
                listing.get('bedrooms', listing.get('beds', 0)), 
                listing.get('bathrooms', listing.get('baths', 0)), 
                listing['sqft'], 
                listing.get('description', ''),
                image_url,
                json.dumps(tags),
                datetime.now()
            ))
            conn.commit()
            print(f"✅ Ingested: {listing.get('address', listing.get('id'))}")
            
        except Exception as e:
            print(f"❌ Error ingesting {listing.get('id')}: {e}")
        finally:
            conn.close()

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        pref = lead.get('preferences', {})
        must_haves = pref.get('must_haves', [])
        
        cursor.execute("""
            INSERT OR REPLACE INTO leads (id, name, phone, max_budget, min_beds, preferred_neighborhood, must_haves)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            lead['id'], 
            lead['name'], 
            lead.get('phone', ''),
            pref.get('budget', 500000), 
            pref.get('bedrooms', 2), 
            pref.get('neighborhood', 'N/A'),
            json.dumps(must_haves)
        ))
        
        conn.commit()
        conn.close()
        print(f"👤 Saved Lead: {lead['name']}")

    def get_lead(self, lead_id: str) -> Optional[Dict]:
        """Retrieves a lead by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        lead = cursor.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        conn.close()
        if lead:
            return dict(lead)
        return None

    # --- Core Logic: Intelligence ---
    def _generate_ai_tags(self, description: str) -> Dict[str, bool]:
        """
        Scans description for features using Anthropic Claude. 
        """
        # Fallback keyword logic
        desc = description.lower()
        keyword_tags = {
            "has_pool": any(x in desc for x in ["pool", "spa", "swim"]),
            "modern_kitchen": any(x in desc for x in ["island", "granite", "quartz", "stainless"]),
            "large_lot": any(x in desc for x in ["acre", "lot", "yard"])
        }

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return keyword_tags

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            
            # Use Claude 3 Haiku for fast, cheap tagging
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                temperature=0,
                system="Extract real estate features from the description. Return ONLY a JSON object with boolean values for: has_pool, modern_kitchen, large_lot. Do not include any other text.",
                messages=[
                    {"role": "user", "content": f"Description: {description}"}
                ]
            )
            
            # Extract JSON from response
            content = message.content[0].text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return keyword_tags
            
        except Exception as e:
            print(f"⚠️ Claude Tagging Failed: {e}. Using keywords.")
            return keyword_tags

    def calculate_match_score(self, lead: sqlite3.Row, property: sqlite3.Row) -> int:
        """
        The Core Algorithm: Returns a 0-100 Score.
        """
        score = 0
        
        # 1. Price Logic (40 Points)
        price_ratio = property['price'] / lead['max_budget']
        if price_ratio > 1.10: # Hard Cap (10% wiggle room)
            return 0 
        
        if 0.8 <= price_ratio <= 1.0:
            score += 40
        elif price_ratio < 0.8:
            score += 30 # Under budget is good
        else:
            score += 20 # Slightly over budget

        # 2. Bedroom Logic (30 Points)
        bed_diff = property['beds'] - lead['min_beds']
        if bed_diff == 0:
            score += 30
        elif bed_diff > 0:
            score += 35 # Bonus!
        elif bed_diff == -1:
            score += 10 # 1 bed short
        else:
            return 0 # Deal breaker (2+ beds short)

        # 3. Features/Tags Logic (30 Points)
        lead_tags = set(json.loads(lead['must_haves'] or "[]"))
        prop_tags = set(json.loads(property['tags'] or "[]"))
        
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        prop = cursor.execute("SELECT * FROM properties WHERE id=?", (property_id,)).fetchone()
        conn.close()
        
        if not prop:
            return None
            
        return {
            "id": prop['id'],
            "address": prop['address'],
            "city": prop['city'],
            "price": prop['price'],
            "beds": prop['beds'],
            "baths": prop['baths'],
            "sqft": prop['sqft'],
            "description": prop['description'],
            "tags": json.loads(prop['tags'] or "[]")
        }

    def get_smart_deck(self, lead_id: str) -> List[Dict]:
        """
        Generates a personalized deck of properties for a specific lead.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        lead = cursor.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        if not lead:
            conn.close()
            return []

        # Get all active properties
        properties = cursor.execute("SELECT * FROM properties WHERE status='Active'").fetchall()
        
        deck = []
        for prop in properties:
            score = self.calculate_match_score(lead, prop)
            if score >= 40: # Slightly lower threshold for the deck
                deck.append({
                    "id": prop['id'],
                    "address": prop['address'],
                    "city": prop['city'],
                    "price": prop['price'],
                    "beds": prop['beds'],
                    "baths": prop['baths'],
                    "sqft": prop['sqft'],
                    "description": prop['description'],
                    "tags": json.loads(prop['tags'] or "[]"),
                    "match_score": score
                })
        
        conn.close()
        # Sort by match score descending
        return sorted(deck, key=lambda x: x['match_score'], reverse=True)

    def log_interaction(self, lead_id: str, property_id: str, action: str, feedback: Optional[Dict] = None, time_on_card: Optional[float] = None):
        """
        Logs a swipe interaction (like/pass) to the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure interactions table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                property_id TEXT,
                action TEXT,
                feedback TEXT,
                time_on_card REAL,
                timestamp DATETIME
            )
        """)
        
        cursor.execute("""
            INSERT INTO interactions (lead_id, property_id, action, feedback, time_on_card, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            lead_id, 
            property_id, 
            action, 
            json.dumps(feedback) if feedback else None, 
            time_on_card,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        print(f"Logged {action} from {lead_id} on {property_id}")

    # --- Runner ---
if __name__ == "__main__":
    # Remove existing db for clean test
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

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
    matches = manager.find_weighted_matches("rc_001")
    print(f"\n--- Matches for {prop['address']['street']} ---")
    for m in matches:
        print(f"🎯 {m['buyer']}: {m['score']}% match (Budget: {m['budget_limit']})")