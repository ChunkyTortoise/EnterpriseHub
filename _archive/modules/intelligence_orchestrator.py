import os
import json
import sqlite3
import anthropic
from dotenv import load_dotenv
from modules.ghl_sync import GHLSyncService

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# This is the Custom Field ID in GHL where we store the "AI Buyer Persona" summary
BUYER_PERSONA_FIELD_ID = os.getenv("BUYER_PERSONA_FIELD_ID", "ghl_field_buyer_persona_id")

def get_db_path():
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return os.getenv("DB_PATH", "real_estate_engine.db")

DATABASE_URL = get_db_path()

# Initialize Anthropic Client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
ghl_service = GHLSyncService()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def synthesize_persona(contact_id):
    """
    1. Fetches all 'liked' properties for a contact.
    2. Aggregates their tags/features.
    3. Uses Claude 3.5 Sonnet to write a 1-sentence persona.
    4. Updates GHL and returns the string for Vapi.
    """
    if not ANTHROPIC_API_KEY:
        return "Interested buyer exploring various options."

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch Liked Properties
    # Note: Using lead_id to match existing interactions table schema
    query = """
    SELECT p.tags, p.price, p.beds, p.baths, p.address
    FROM interactions i
    JOIN properties p ON i.property_id = p.id
    WHERE i.lead_id = ? AND i.action = 'like'
    """
    cursor.execute(query, (contact_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "New lead with no specific preferences yet."

    # 2. Prepare Data for AI
    liked_homes = []
    for row in rows:
        # safely parse tags if they are stored as JSON strings
        try:
            tags = json.loads(row['tags']) if row['tags'] else []
        except:
            tags = [row['tags']] # Fallback for simple strings

        liked_homes.append({
            "address": row['address'],
            "price": row['price'],
            "specs": f"{row['beds']}bd/{row['baths']}ba",
            "tags": tags
        })

    # 3. Prompt Claude 3.5 Sonnet
    prompt = f"""
    Here is a list of properties a real estate lead has 'Liked':
    {json.dumps(liked_homes, indent=2)}

    Based ONLY on this data, write a ONE-SENTENCE 'Buyer Persona' summary for a real estate agent.
    Focus on architectural style, price point, and key features they seem to value.
    Example: "High-budget buyer targeting mid-century modern homes with pools in the Palm Springs area."
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        persona_text = response.content[0].text.strip()
        print(f"🧠 Generated Persona: {persona_text}")

        # 4. Write-Back to GHL
        ghl_service.update_contact_field(contact_id, BUYER_PERSONA_FIELD_ID, persona_text)
        
        return persona_text

    except Exception as e:
        print(f"❌ Intelligence Error: {e}")
        return "Interested buyer exploring various options."

# Example Usage
if __name__ == "__main__":
    # Test with a dummy ID if running directly
    print(synthesize_persona("test_contact_123"))
