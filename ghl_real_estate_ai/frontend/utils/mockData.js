/**
 * Mock Property Data for Testing
 * 
 * Use this data to test the swipe interface locally before connecting to real API.
 */

export const mockProperties = [
  {
    id: "prop_001",
    price: 485000,
    beds: 3,
    baths: 2,
    sqft: 1850,
    address: "1234 Ocean View Dr",
    city: "San Diego",
    state: "CA",
    property_type: "Single Family",
    image_url: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop",
    est_payment: 3200,
    status: "New Listing"
  },
  {
    id: "prop_002",
    price: 625000,
    beds: 4,
    baths: 3,
    sqft: 2400,
    address: "5678 Sunset Blvd",
    city: "Los Angeles",
    state: "CA",
    property_type: "Modern Contemporary",
    image_url: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop",
    est_payment: 4100
  },
  {
    id: "prop_003",
    price: 399000,
    beds: 2,
    baths: 2,
    sqft: 1400,
    address: "910 Maple Street",
    city: "Sacramento",
    state: "CA",
    property_type: "Condo",
    image_url: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop",
    est_payment: 2650,
    status: "Price Drop"
  },
  {
    id: "prop_004",
    price: 750000,
    beds: 5,
    baths: 4,
    sqft: 3200,
    address: "2468 Highland Ave",
    city: "San Francisco",
    state: "CA",
    property_type: "Victorian",
    image_url: "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&h=600&fit=crop",
    est_payment: 4900
  },
  {
    id: "prop_005",
    price: 550000,
    beds: 3,
    baths: 2.5,
    sqft: 2100,
    address: "1357 Beach Rd",
    city: "Santa Monica",
    state: "CA",
    property_type: "Townhouse",
    image_url: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop",
    est_payment: 3650
  }
];

/**
 * Mock API Response
 * Simulates the backend response structure
 */
export const mockSwipeResponse = {
  like: {
    status: "logged",
    trigger_sms: false,
    high_intent: false,
    message: null
  },
  pass: {
    status: "preference_updated",
    adjustments: ["Lowered budget to $450,000"],
    trigger_sms: false,
    high_intent: false
  },
  highIntent: {
    status: "logged",
    trigger_sms: true,
    high_intent: true,
    message: "High intent detected: 3 likes in 10 minutes"
  }
};

/**
 * Mock Lead Data
 */
export const mockLead = {
  id: "contact_demo_123",
  name: "John Doe",
  email: "john@example.com",
  location_id: "loc_demo"
};
