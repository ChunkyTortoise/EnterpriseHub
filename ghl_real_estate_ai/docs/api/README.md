# API Documentation

## Overview
REST API for GHL Real Estate AI Platform

## Endpoints

### Authentication
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout

### Leads
- GET /api/leads
- POST /api/leads
- GET /api/leads/:id
- PUT /api/leads/:id
- DELETE /api/leads/:id

### Analytics
- GET /api/analytics/dashboard
- GET /api/analytics/revenue
- GET /api/analytics/campaigns

### Workflows
- GET /api/workflows
- POST /api/workflows
- PUT /api/workflows/:id

## API Files Found: 11


### auth.py
Location: `api/routes/auth.py`

### portal.py
Location: `api/routes/portal.py`

### webhook.py
Location: `api/routes/webhook.py`

### properties.py
Location: `api/routes/properties.py`

### crm.py
Location: `api/routes/crm.py`

### lead_lifecycle.py
Location: `api/routes/lead_lifecycle.py`

### __init__.py
Location: `api/routes/__init__.py`

### team.py
Location: `api/routes/team.py`

### voice.py
Location: `api/routes/voice.py`

### analytics.py
Location: `api/routes/analytics.py`

### bulk_operations.py
Location: `api/routes/bulk_operations.py`
