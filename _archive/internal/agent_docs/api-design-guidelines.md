# API Design Guidelines

## REST Endpoints
- Use **GET** for reads, **POST** for creates, **PATCH** for updates, **DELETE** for deletes
- Always wrap responses: `{ success: boolean, data?, error? }`
- Rate limit sensitive endpoints: login (10/min), API key (100/hour)
- Return `201 Created` for POST, `200 OK` for others

## Error Responses
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required"
  }
}
```

## Authentication
- Use JWT: `Authorization: Bearer <token>`
- Token expiry: 15 minutes (access), 7 days (refresh)
- Store refresh tokens in httpOnly cookies
- Validate user ownership before resource access
