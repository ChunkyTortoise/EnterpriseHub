# Deployment Checklist

## Environment Setup
- [ ] Python 3.11+ installed
- [ ] All dependencies installed (requirements.txt)
- [ ] .env file configured with real API keys
- [ ] Environment validation passes

## Required API Keys
- [ ] Anthropic API key (ANTHROPIC_API_KEY)
- [ ] GoHighLevel API key (GHL_API_KEY)
- [ ] GoHighLevel Location ID (GHL_LOCATION_ID)
- [ ] Database URL configured (DATABASE_URL)
- [ ] JWT Secret key set (JWT_SECRET_KEY)

## Security Configuration
- [ ] JWT secret is 32+ characters in production
- [ ] Webhook secrets configured (32+ characters)
- [ ] Redis password set for production
- [ ] ENVIRONMENT variable set correctly

## Optional Services (Configure if needed)
- [ ] Stripe API keys for billing
- [ ] Twilio credentials for SMS
- [ ] SendGrid API key for email
- [ ] Voice AI providers (Vapi/Retell)

## Database Setup
- [ ] PostgreSQL database created
- [ ] Database migrations run
- [ ] Redis server running
- [ ] Connection pooling configured

## Testing
- [ ] Environment validation passes
- [ ] Application starts successfully
- [ ] Core features working
- [ ] API endpoints responding

## Production Deployment
- [ ] Environment set to "production"
- [ ] Debug mode disabled
- [ ] CORS configured for production domains
- [ ] Health checks configured
- [ ] Monitoring and logging set up

## Performance Optimizations
- [ ] Phase 1-4 optimizations enabled
- [ ] Token budget limits configured
- [ ] Semantic caching enabled
- [ ] Database connection pooling active

Run these commands to validate:
1. python3 setup_deployment.py
2. python3 validate_environment.py
3. streamlit run app.py

For issues, check the generated validation report.