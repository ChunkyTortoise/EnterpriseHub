# 🔌 GHL Real Estate AI - API Documentation

**Version:** 1.0.0
**Base URL:** `https://your-app-url.railway.app/api`

---

## 🔐 Authentication

Most endpoints require authentication.

### **JWT Authentication (Bearer Token)**
Use the `/api/auth/login` endpoint to get an access token.
Include the token in the header:
`Authorization: Bearer <your_token>`

### **API Key Authentication**
For server-to-server communication (e.g., from GHL webhooks).
Include headers:
- `X-API-Key`: Your API key
- `X-Location-ID`: Your GHL Location ID

---

## 📡 Endpoints

### **1. Authentication**

#### `POST /auth/login`
Get a JWT access token.
- **Body:**
  ```json
  {
    "username": "admin",
    "password": "your_password"
  }
  ```

### **2. Webhook (GHL Integration)**

#### `POST /ghl/webhook`
Handle incoming messages from GoHighLevel.
- **Body:** JSON payload from GHL webhook automation.
- **Returns:** AI response and list of actions (tags, custom field updates).

### **3. Analytics**

#### `GET /analytics/dashboard`
Get high-level dashboard metrics.
- **Query Params:** `location_id`, `days` (default: 7)
- **Response:**
  ```json
  {
    "total_conversations": 150,
    "avg_lead_score": 7.5,
    "conversion_rate": 0.12,
    "hot_leads": 15
  }
  ```

#### `GET /analytics/campaigns/{location_id}`
Get performance metrics for all campaigns.

#### `POST /analytics/optimize/next-question`
Get AI suggestion for the next best question to ask.
- **Body:**
  ```json
  {
    "conversation_history": ["..."],
    "current_lead_score": 5,
    "questions_answered": ["budget", "location"]
  }
  ```

### **4. Team Management**

#### `GET /team/{location_id}/agents`
List all agents in a location.

#### `POST /team/{location_id}/agents`
Add a new agent.
- **Body:**
  ```json
  {
    "id": "agent_123",
    "name": "Sarah Jones",
    "email": "sarah@example.com",
    "role": "agent"
  }
  ```

#### `POST /team/{location_id}/assign`
Assign a lead to an agent (round-robin or smart assignment).
- **Query Params:** `contact_id`

### **5. Lead Lifecycle**

#### `GET /lifecycle/journeys`
Get all active lead journeys.

#### `GET /lifecycle/stats`
Get aggregate lifecycle statistics.

---

## 🛠️ Error Handling

The API returns standard HTTP status codes:
- **200 OK**: Request successful.
- **400 Bad Request**: Invalid input.
- **401 Unauthorized**: Missing or invalid token.
- **403 Forbidden**: Insufficient permissions.
- **404 Not Found**: Resource not found.
- **422 Validation Error**: Request body does not match schema.
- **500 Internal Server Error**: Unexpected server error.

All errors return a JSON object:
```json
{
  "success": false,
  "error": "Error Type",
  "detail": "Detailed error message",
  "request_id": "req_12345"
}
```