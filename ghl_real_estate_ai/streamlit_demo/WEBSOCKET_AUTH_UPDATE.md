# Streamlit WebSocket Authentication Update Guide

## SECURITY UPDATE REQUIRED

The `streamlit_demo/components/websocket_integration.py` file currently uses hardcoded `demo_token_jorge` authentication at line 58.

### Production Fix Required

**Location**: Line 55-61 in websocket_integration.py

**Current Code**:
```javascript
// Authenticate with demo credentials
this.send({
    'type': 'auth',
    'token': 'demo_token_jorge',
    'user_id': 'jorge_dashboard',
    'role': 'admin'
});
```

**Recommended Fix**:
```javascript
// PRODUCTION: Authenticate with proper JWT token
// Obtain token from sessionStorage or auth endpoint
const authToken = sessionStorage.getItem('jorge_auth_token') || 'demo_token_jorge';
if (!sessionStorage.getItem('jorge_auth_token')) {
    console.warn('[WebSocket] No auth token in sessionStorage. Demo mode - will fail in production.');
    console.warn('[WebSocket] Set: sessionStorage.setItem("jorge_auth_token", yourJWT)');
}

this.send({
    'type': 'auth',
    'token': authToken,
    'user_id': 'jorge_dashboard',
    'role': 'admin'
});
```

### Why This Matters

With the production security hardening:
- `demo_token_jorge` will be **REJECTED** unless `ENABLE_DEMO_BYPASS=true` is explicitly set
- In production, this WebSocket connection will fail unless proper JWT is provided
- Use `sessionStorage.setItem('jorge_auth_token', yourJWT)` before loading the dashboard

### How to Obtain Valid JWT

```python
# In Streamlit app, after user logs in:
from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service

# After successful authentication
auth_response = await enterprise_auth_service.handle_sso_callback(code, state)
jwt_token = auth_response['access_token']

# Pass to JavaScript
st.markdown(f"""
<script>
sessionStorage.setItem('jorge_auth_token', '{jwt_token}');
</script>
""", unsafe_allow_html=True)
```

## Manual Edit Instructions

Since the file contains complex f-string formatting with embedded JavaScript, manual editing is recommended:

1. Open `ghl_real_estate_ai/streamlit_demo/components/websocket_integration.py`
2. Find line 55-61 (the `this.send()` auth block)
3. Replace with the recommended fix code above
