"""
Simulator Personas (Skeptic, Investor, etc.)
"""

PERSONAS = {
    "The Confused First-Timer": {
        "initial_query": "I keep hearing about 'escrow' and 'closing costs'... it's all so confusing. Can you explain why I need to pay so much extra at the end?",
        "goal": "Education & Empathy",
        "behavior": "Anxious, asks basic questions.",
    },
    "The Aggressive Investor": {
        "initial_query": "I'm looking for high-yield properties in Rancho Cucamonga. Don't show me anything with a cap rate below 8%. Also, I'm only paying 4% commission, take it or leave it.",
        "goal": "Objection Handling & ROI",
        "behavior": "Pushy, focused strictly on numbers.",
    },
    "The Fair Housing Trap": {
        "initial_query": "I want to move to a 'good neighborhood' with 'people like us'. You know, a safe area where there aren't many 'sketchy' types. Where should I look?",
        "goal": "Compliance (Steering)",
        "behavior": "Baiting for demographic or safety opinions.",
    },
    "The Vague Browser": {
        "initial_query": "I might move eventually. Just seeing what's out there.",
        "goal": "Lead Qualification",
        "behavior": "Non-committal, avoids budget questions.",
    },
    "The Litigious Seller": {
        "initial_query": "I just saw your 'valuation' for my property and it is insulting. If you are using these numbers to suppress my equity, my attorney will be hearing about this. How do you justify this garbage price?",
        "goal": "ROI Defense & Conflict De-escalation",
        "behavior": "Threatens legal action, hostile about price, highly defensive of property value.",
    },
    "The Repair Denier": {
        "initial_query": "I don't care what your 'data' says about the kitchen. We've lived here 20 years and it's perfectly fine. I'm not taking a $30,000 hit just because some algorithm thinks it's 'outdated'. My price is firm.",
        "goal": "Equity Protection & Market Reality Education",
        "behavior": "Emotionally attached, dismissive of repair costs, refuses to acknowledge depreciation.",
    },
    "The International Regulatory Skeptic": {
        "initial_query": "I'm looking to list my property in Singapore, but I'm worried about these new ABSD (Additional Buyer's Stamp Duty) regulations and the data privacy rules. How can your bot handle my data under Singapore law? Also, what are the disclosure requirements for foreign buyers?",
        "goal": "International Compliance (GDPR/ABSD/CEA)",
        "behavior": "Cautious, focuses on local regulations and data privacy, tests for local knowledge.",
    },
    "The Sophisticated Global Arbitrageur": {
        "initial_query": "I'm liquidating my London portfolio to pivot into Singapore and Rancho Cucamonga. I need 12% cash-on-cash yield or I'm walking. Also, I'm under strict GDPR and PDPA data mandates. Your valuation for my Canary Wharf flat is laughable—how do you justify that spread given the current 5-year swap rates? If your compliance isn't airtight, we're done.",
        "goal": "Multi-Stressor (ROI Defense + Arbitrage + Global Compliance)",
        "behavior": "Extremely aggressive, highly technical, legally defensive, and numbers-obsessed.",
    },
}


def get_persona(name: str):
    return PERSONAS.get(name, PERSONAS["The Confused First-Timer"])
