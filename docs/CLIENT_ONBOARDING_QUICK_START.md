# 🚀 Customer Intelligence Platform - Client Onboarding Quick Start Guide

**Get your Customer Intelligence Platform up and running in 30 minutes or less!**

---

## 📋 Pre-Requisites Checklist

Before you begin, ensure you have:

- [ ] **System Requirements**: Docker & Docker Compose installed
- [ ] **API Keys**: Anthropic Claude API key for AI features
- [ ] **Database Access**: PostgreSQL instance (local or cloud)
- [ ] **Cache Service**: Redis instance (included in Docker setup)
- [ ] **Admin Access**: Ability to create user accounts and configure tenants

---

## 🎯 30-Minute Setup Process

### Phase 1: Environment Setup (5 minutes)

#### Step 1: Clone and Navigate
```bash
git clone <repository-url>
cd EnterpriseHub
```

#### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```bash
# AI Configuration (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-api03-your-claude-api-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/enterprisehub
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secure-32-character-secret-key-here

# Application Settings
STREAMLIT_SERVER_PORT=8501
ENVIRONMENT=production
USE_DEMO_DATA=false
```

### Phase 2: Database & Services Initialization (10 minutes)

#### Step 3: Start Infrastructure Services
```bash
# Start Redis and PostgreSQL
docker-compose up -d redis

# For PostgreSQL (if using local Docker)
docker run -d \
  --name customer-intelligence-postgres \
  -e POSTGRES_USER=username \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=enterprisehub \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Step 4: Database Migration
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -c "
from ghl_real_estate_ai.database.migrations import run_migrations
run_migrations()
"
```

#### Step 5: Create Initial Tenant
```bash
# Create default tenant
python -c "
from ghl_real_estate_ai.services.tenant_service import TenantService
tenant_service = TenantService()
tenant_service.create_tenant(
    tenant_id='your_company',
    name='Your Company Name',
    settings={'theme': 'default', 'analytics_enabled': True}
)
"
```

### Phase 3: Application Deployment (10 minutes)

#### Step 6: Build and Start Application
```bash
# Build Docker image
docker-compose build

# Start application stack
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### Step 7: Health Check
```bash
# Check application health
curl http://localhost:8501/health

# Check Redis connection
redis-cli ping

# Check database connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Phase 4: User Setup & Configuration (5 minutes)

#### Step 8: Access Application
1. Open browser to `http://localhost:8501`
2. You should see the Customer Intelligence Platform login screen

#### Step 9: Create Admin User
```bash
# Create admin user
python -c "
from ghl_real_estate_ai.services.user_management import create_admin_user
create_admin_user(
    username='admin',
    password='secure_password_123',
    tenant_id='your_company',
    email='admin@yourcompany.com'
)
"
```

#### Step 10: Initial Login & Configuration
1. **Login** with admin credentials
2. **Verify tenant** selection shows "your_company"
3. **Access dashboards** - confirm all 4 dashboards load:
   - 🎯 Real-Time Analytics
   - 👥 Customer Segmentation  
   - 🗺️ Journey Mapping
   - 🏢 Enterprise Tenant

---

## ✅ Post-Setup Verification

### System Health Checklist

- [ ] **Application Status**: Platform loads at `http://localhost:8501`
- [ ] **Authentication**: Admin login successful
- [ ] **Database**: Connection established and migrations complete
- [ ] **Redis Cache**: Connected and responding
- [ ] **AI Services**: Claude API key validated
- [ ] **Dashboard Access**: All dashboards render without errors

### Test Data Verification

#### Load Sample Data
```bash
# Load sample customer data for testing
python -c "
from ghl_real_estate_ai.services.demo_state import DemoState
demo = DemoState()
demo.generate_sample_customer_data(tenant_id='your_company', count=100)
"
```

#### Verify Analytics
1. Go to **Real-Time Analytics** dashboard
2. Confirm sample data appears in:
   - Customer overview cards
   - Revenue analytics charts
   - Lead scoring metrics
   - Activity timeline

---

## 🎨 Initial Configuration

### Tenant Customization

#### Brand Settings
1. Navigate to **Enterprise Tenant** dashboard
2. Upload company logo
3. Set brand colors and theme
4. Configure company information

#### User Roles & Permissions
```bash
# Create additional users
python scripts/create_user.py \
  --username analyst1 \
  --password analyst_pass \
  --role analyst \
  --tenant your_company \
  --email analyst@yourcompany.com

python scripts/create_user.py \
  --username viewer1 \
  --password viewer_pass \
  --role viewer \
  --tenant your_company \
  --email viewer@yourcompany.com
```

### Integration Setup

#### CRM Integration (Optional)
If using GoHighLevel:
```bash
# Add GHL configuration to .env
echo "GHL_API_KEY=your-ghl-api-key" >> .env
echo "LOCATION_ID=your-ghl-location-id" >> .env

# Restart application
docker-compose restart app
```

#### Analytics Configuration
```bash
# Configure analytics preferences
python -c "
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
analytics = AnalyticsService()
analytics.configure_tenant_analytics(
    tenant_id='your_company',
    settings={
        'real_time_enabled': True,
        'data_retention_days': 365,
        'export_formats': ['csv', 'json', 'pdf']
    }
)
"
```

---

## 🔧 Troubleshooting Quick Fixes

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose logs app

# Common fixes:
# 1. Verify environment variables
cat .env | grep -E "(ANTHROPIC_API_KEY|DATABASE_URL|REDIS_URL)"

# 2. Reset containers
docker-compose down
docker-compose up -d
```

#### Database Connection Issues
```bash
# Test database connectivity
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
engine.connect()
print('Database connection successful')
"
```

#### Redis Connection Issues
```bash
# Test Redis connectivity
redis-cli -u $REDIS_URL ping

# If Redis is down, restart
docker-compose restart redis
```

#### Login Issues
```bash
# Reset admin password
python -c "
from ghl_real_estate_ai.services.user_management import reset_password
reset_password('admin', 'new_password_123')
"
```

### Performance Issues

#### Slow Dashboard Loading
1. Check Redis cache status: `redis-cli info memory`
2. Verify adequate system resources: `docker stats`
3. Restart application: `docker-compose restart app`

#### High Memory Usage
```bash
# Check container resource usage
docker stats

# Optimize memory settings in docker-compose.yml
# Add memory limits:
# services:
#   app:
#     mem_limit: 2g
#   redis:
#     mem_limit: 512m
```

---

## 📞 Support & Next Steps

### Immediate Support
- **Technical Issues**: Check logs first: `docker-compose logs`
- **Configuration Help**: Refer to `.env.example` for all options
- **User Management**: Use provided Python scripts in `scripts/` directory

### Next Steps After Setup
1. **Data Integration**: Connect your existing customer data sources
2. **User Training**: Review the User Training Materials (next document)
3. **Performance Monitoring**: Set up monitoring dashboards
4. **Backup Configuration**: Implement backup procedures

### Success Metrics to Track
- **Login Success Rate**: Should be >99%
- **Dashboard Load Time**: Should be <3 seconds
- **Data Freshness**: Real-time updates within 30 seconds
- **User Adoption**: Track active users in first week

---

## 🎉 Congratulations!

Your Customer Intelligence Platform is now live and ready for production use!

**What's Next?**
- Review the **Technical Implementation Guide** for advanced configuration
- Complete the **User Training Materials** for your team
- Set up **Performance Monitoring** using the Client Success Enablement Kit

**Need Help?** Contact your implementation specialist or refer to the comprehensive documentation suite included with your platform.

---

*Customer Intelligence Platform - Enterprise Edition*  
*© 2026 - Production Ready*