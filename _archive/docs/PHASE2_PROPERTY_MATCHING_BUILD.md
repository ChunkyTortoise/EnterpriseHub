# Phase 2: Smart Property Matching - Build Plan

**Date**: 2026-01-06  
**Status**: Ready to Build  
**Timeline**: 1 week  
**Priority**: HIGH (Jorge requested this feature)

---

## 🎯 Objective

Build an AI-powered property matching system that:
1. Automatically matches buyers with properties based on their criteria
2. Sends personalized property recommendations via GHL
3. Syncs with buyer preferences stored in Phase 1
4. Operates entirely within GHL ecosystem

---

## 📋 Requirements (From Jorge)

> "AI bot that qualifies buyers and sends them homes based on their criteria that they're looking for. All within GHL."

### Core Features Needed:
- ✅ Buyer qualification (Phase 1 - COMPLETE)
- 🔨 Property search/matching engine (Phase 2 - THIS)
- 🔨 Self-service portal (Phase 3 - Next)
- 🔨 Intelligent follow-up (Phase 4 - Future)

---

## 🏗️ Technical Architecture

### New Services to Build

#### 1. `property_search_service.py`
**Purpose**: Search and filter properties based on buyer criteria

```python
class PropertySearchService:
    def search_properties(self, criteria: BuyerCriteria) -> List[Property]:
        """
        Search properties matching buyer criteria
        
        Criteria includes:
        - Budget range (min/max)
        - Location (city, neighborhood, zip)
        - Beds/baths (min)
        - Property type (single-family, condo, etc.)
        - Square footage
        - Additional features
        """
        pass
    
    def rank_properties(self, properties: List[Property], buyer_profile) -> List[Property]:
        """Score and rank properties by match quality (0-100)"""
        pass
    
    def get_new_listings(self, since_timestamp: datetime) -> List[Property]:
        """Get new listings since last check"""
        pass
```

#### 2. `property_matcher_ai.py`
**Purpose**: AI-powered matching and recommendation engine

```python
class PropertyMatcherAI:
    def generate_property_recommendations(self, buyer_id: str, num_properties: int = 5):
        """
        Generate personalized property recommendations
        - Pulls buyer preferences from Phase 1
        - Searches available properties
        - Ranks by match score
        - Generates personalized descriptions
        """
        pass
    
    def generate_recommendation_message(self, buyer, properties) -> str:
        """
        Generate personalized message for buyer
        Example: "Hey Sarah, I found 3 perfect homes in Miami Beach under $400K..."
        """
        pass
    
    def update_buyer_matches(self, buyer_id: str):
        """Update matches when new listings arrive or criteria changes"""
        pass
```

#### 3. `ghl_property_sync.py`
**Purpose**: Sync property data and send recommendations via GHL

```python
class GHLPropertySync:
    def send_property_matches(self, contact_id: str, properties: List[Property]):
        """
        Send property matches to buyer via GHL
        - SMS with property links
        - Email with full details
        - Update custom fields
        """
        pass
    
    def track_engagement(self, contact_id: str, property_id: str, action: str):
        """Track buyer engagement (opened, clicked, favorited)"""
        pass
    
    def schedule_followup(self, contact_id: str, properties: List[Property]):
        """Schedule automated follow-up workflow in GHL"""
        pass
```

---

## 🗂️ Data Models

### Property Model
```python
@dataclass
class Property:
    id: str
    mls_id: Optional[str]
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: int
    property_type: str  # single-family, condo, townhouse, etc.
    description: str
    features: List[str]
    images: List[str]
    listing_date: datetime
    status: str  # active, pending, sold
    agent_contact: str
```

### BuyerCriteria Model (from Phase 1)
```python
@dataclass
class BuyerCriteria:
    buyer_id: str
    min_price: float
    max_price: float
    location: List[str]  # cities, neighborhoods, zips
    min_bedrooms: int
    min_bathrooms: float
    property_types: List[str]
    must_have_features: List[str]
    nice_to_have_features: List[str]
    timeline: str  # immediate, 1-3 months, 3-6 months, etc.
```

### PropertyMatch Model
```python
@dataclass
class PropertyMatch:
    match_id: str
    buyer_id: str
    property_id: str
    match_score: int  # 0-100
    match_reasons: List[str]  # ["Perfect price match", "In preferred neighborhood"]
    sent_date: Optional[datetime]
    engagement: Optional[dict]  # opened, clicked, favorited, etc.
```

---

## 📁 File Structure

```
ghl_real_estate_ai/
├── services/
│   ├── property_search_service.py        # NEW
│   ├── property_matcher_ai.py            # NEW
│   ├── ghl_property_sync.py              # NEW
│   └── ai_predictive_lead_scoring.py     # EXISTING (integrate with)
│
├── api/routes/
│   ├── properties.py                     # NEW
│   └── buyer_matches.py                  # NEW
│
├── data/
│   ├── properties/                       # NEW
│   │   ├── listings.json
│   │   └── matches.json
│   └── crm/
│       └── buyer_criteria.json           # EXISTING (from Phase 1)
│
└── tests/
    ├── test_property_search.py           # NEW
    ├── test_property_matcher_ai.py       # NEW
    └── test_ghl_property_sync.py         # NEW
```

---

## 🔄 Integration Points

### With Phase 1 (Buyer Qualification)
- Read buyer criteria from `ai_predictive_lead_scoring.py`
- Access buyer profiles from GHL CRM
- Use lead scores to prioritize matches

### With GHL
- **Custom Fields**: Store matched properties
- **Tags**: Add "Has Matches", "Viewed Properties", "Hot Buyer"
- **Workflows**: Trigger "Send Property Matches" workflow
- **SMS/Email**: Send personalized recommendations
- **Appointments**: Book showing appointments

### With Existing Services
- `crm_service.py`: Access buyer data
- `ghl_sync_service.py`: Sync property data
- `memory_service.py`: Store match history
- `analytics_service.py`: Track match performance

---

## 🚀 Implementation Steps

### Week 1: Core Property Matching

#### Day 1-2: Data Foundation
- [ ] Create Property data model
- [ ] Create PropertyMatch data model
- [ ] Build property storage system (JSON initially, DB later)
- [ ] Create sample property dataset (20-30 listings)
- [ ] Set up GHL custom fields for properties

#### Day 3-4: Search & Matching Engine
- [ ] Build `PropertySearchService`
  - [ ] Implement basic search (price, location, beds/baths)
  - [ ] Add advanced filters (property type, features)
  - [ ] Build ranking algorithm
- [ ] Build `PropertyMatcherAI`
  - [ ] Integrate with Anthropic Claude for personalized descriptions
  - [ ] Create match scoring algorithm
  - [ ] Build recommendation generator

#### Day 5-6: GHL Integration
- [ ] Build `GHLPropertySync`
  - [ ] Send properties via SMS
  - [ ] Send properties via Email
  - [ ] Update GHL contact fields
  - [ ] Track engagement
- [ ] Create API endpoints
  - [ ] `POST /api/properties` (add listing)
  - [ ] `GET /api/properties/search` (search properties)
  - [ ] `GET /api/buyers/{id}/matches` (get buyer matches)
  - [ ] `POST /api/buyers/{id}/matches/send` (send matches)

#### Day 7: Testing & Demo
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test with Jorge's GHL account
- [ ] Create demo scenario
- [ ] Document API usage

---

## 🎬 Demo Scenarios

### Scenario 1: New Buyer Gets Instant Matches
```
1. Sarah qualifies via AI bot (Phase 1)
   - Budget: $350K-$450K
   - Location: Miami Beach
   - Beds: 3+, Baths: 2+
   
2. AI instantly searches properties
   - Finds 5 matches
   - Scores each 85-95/100
   
3. AI sends personalized SMS:
   "Hi Sarah! Great news - I found 5 perfect homes in Miami Beach 
   that match your criteria. All 3BR/2BA, $350-$425K. Want to see them?"
   
4. Sarah clicks link → sees properties with details
```

### Scenario 2: New Listing Matches Multiple Buyers
```
1. Jorge adds new listing to system
   - $380K, 3BR/2BA, Miami Beach condo
   
2. AI searches all buyers
   - Finds 12 buyers matching criteria
   - Ranks by lead score (Phase 1)
   
3. AI sends to top 5 buyers:
   "Hot new listing just hit the market! 3BR/2BA condo in Miami Beach 
   at $380K - exactly what you're looking for. Want details?"
```

### Scenario 3: Buyer Updates Criteria
```
1. Sarah's budget increases to $500K
   
2. AI re-runs search automatically
   - Finds 8 new matches
   
3. AI sends update:
   "I noticed your budget increased! I found 8 more homes that fit 
   your updated criteria. Check them out?"
```

---

## 🔌 API Examples

### Add Property
```bash
POST /api/properties
{
  "address": "123 Ocean Drive",
  "city": "Miami Beach",
  "state": "FL",
  "zip_code": "33139",
  "price": 380000,
  "bedrooms": 3,
  "bathrooms": 2,
  "square_feet": 1500,
  "property_type": "condo",
  "description": "Beautiful oceanfront condo...",
  "features": ["ocean view", "pool", "garage"],
  "images": ["url1", "url2"],
  "agent_contact": "jorge@example.com"
}
```

### Search Properties
```bash
GET /api/properties/search?min_price=350000&max_price=450000&city=Miami+Beach&bedrooms=3
```

### Get Buyer Matches
```bash
GET /api/buyers/{ghl_contact_id}/matches
```

### Send Matches to Buyer
```bash
POST /api/buyers/{ghl_contact_id}/matches/send
{
  "num_properties": 5,
  "channel": "sms"  # or "email" or "both"
}
```

---

## 📊 Success Metrics

### Technical Metrics
- [ ] Search returns results < 500ms
- [ ] Match accuracy > 85% (buyer engagement)
- [ ] GHL sync success rate > 95%
- [ ] API uptime > 99%

### Business Metrics
- [ ] Average 5-7 matches per qualified buyer
- [ ] 40%+ open rate on property messages
- [ ] 20%+ click-through rate
- [ ] 10%+ booking rate for showings

---

## 🔐 Security Considerations

- [ ] Validate property data before storage
- [ ] Sanitize search inputs
- [ ] Rate limit API endpoints
- [ ] Encrypt sensitive property data
- [ ] Audit trail for property views

---

## 📝 Jorge Integration Checklist

Before deploying to Jorge:
- [ ] Test with his GHL account
- [ ] Configure his custom fields
- [ ] Set up his workflows
- [ ] Import his property listings
- [ ] Test with real buyer data
- [ ] Verify SMS/email delivery
- [ ] Train him on property management

---

## 🚧 Known Limitations & Future Enhancements

### Current Limitations
- Manual property input (no MLS integration yet)
- Basic search algorithm (no AI-powered semantic search)
- Limited to GHL's native features

### Phase 3 Enhancements (Self-Service Portal)
- Buyer can update criteria themselves
- Interactive property filtering
- Save favorites
- Schedule showings

### Phase 4 Enhancements (Intelligent Follow-Up)
- Automated nurture sequences
- Price drop alerts
- Similar property suggestions
- Behavioral triggers

---

## 🆘 Troubleshooting

### Common Issues

**Properties not appearing in searches:**
- Check property status is "active"
- Verify GHL sync is working
- Check search criteria ranges

**Matches not sending:**
- Verify GHL API credentials
- Check buyer has valid phone/email
- Verify workflow is enabled

**Low match scores:**
- Review matching algorithm weights
- Check buyer criteria completeness
- Adjust scoring thresholds

---

## 📞 Next Steps

1. **Review this plan** - Make sure it matches Jorge's vision
2. **Get property data source** - How will Jorge input listings?
3. **Start Day 1 tasks** - Begin building data foundation
4. **Daily check-ins** - 15-min sync with Jorge

---

## 💬 Questions for Jorge

Before starting, confirm:

1. **Property Data Source**:
   - Will you manually add listings?
   - Do you have MLS access/feed?
   - How many active listings typically?

2. **Matching Logic**:
   - How strict on budget (±10%? ±20%)?
   - How many matches to send initially?
   - How often to send new matches?

3. **Communication Preferences**:
   - SMS, email, or both?
   - Time of day to send matches?
   - Frequency limits?

4. **Integration Timeline**:
   - When do you need this live?
   - Can we test with real buyers?
   - Who manages property updates?

---

**Ready to build! Let's ship Phase 2. 🚀**
