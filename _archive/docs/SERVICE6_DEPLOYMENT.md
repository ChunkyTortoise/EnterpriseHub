# SERVICE 6 DEPLOYMENT GUIDE
## One-Command Production Deployment on DigitalOcean

---

**Purpose**: Complete deployment guide for the Lead Recovery & Nurture Engine automation system.
**Target Environment**: Production-ready DigitalOcean infrastructure
**Deployment Time**: 15-20 minutes from start to fully operational
**Cost**: $12/month infrastructure + API costs (~$50-150/month based on volume)

---

## QUICK START DEPLOYMENT

### Prerequisites Checklist
- [ ] DigitalOcean account with payment method
- [ ] Domain name for the system (optional but recommended)
- [ ] API credentials for integrations (see API Requirements section)
- [ ] SSH key pair for server access

### One-Command Deployment
```bash
# Clone deployment repository and run automated setup
curl -fsSL https://raw.githubusercontent.com/service6-automation/deploy/main/deploy.sh | bash
```

**What this script does**:
1. Creates DigitalOcean droplet ($12/month)
2. Installs Docker and docker-compose
3. Configures SSL certificates (Let's Encrypt)
4. Deploys n8n + PostgreSQL + Redis + Nginx
5. Sets up monitoring and backups
6. Configures security and firewall

### Alternative Manual Deployment
If you prefer step-by-step control, continue with the detailed deployment section below.

---

## DETAILED DEPLOYMENT PROCESS

### Step 1: DigitalOcean Infrastructure Setup

#### 1.1 Create Droplet
```bash
# Using DigitalOcean CLI (doctl)
doctl compute droplet create service6-automation \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb \
  --region nyc3 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --enable-monitoring \
  --enable-private-networking \
  --tag-names production,automation
```

**Recommended Specifications**:
- **Instance Type**: Basic Droplet ($24/month) or CPU-Optimized ($12/month)
- **CPU**: 2 vCPUs
- **Memory**: 4GB RAM
- **Storage**: 80GB SSD
- **Bandwidth**: 4TB transfer
- **Region**: Choose closest to your target market

#### 1.2 Domain Configuration (Optional)
```bash
# Point your domain to the droplet IP
# A Record: automation.yourdomain.com → DROPLET_IP
# Alternatively, use droplet IP directly for testing
```

### Step 2: Server Preparation

#### 2.1 Initial Server Setup
```bash
# SSH into your new droplet
ssh root@YOUR_DROPLET_IP

# Update system packages
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git unzip software-properties-common

# Create application user
useradd -m -s /bin/bash service6
usermod -aG sudo service6
su - service6
```

#### 2.2 Docker Installation
```bash
# Install Docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker service6

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### Step 3: Application Deployment

#### 3.1 Clone Repository and Configuration
```bash
# Clone the Service 6 deployment repository
git clone https://github.com/service6-automation/lead-engine.git /home/service6/automation
cd /home/service6/automation

# Copy environment template
cp .env.example .env

# Generate secure passwords
openssl rand -base64 32  # Use for DB_PASSWORD
openssl rand -base64 32  # Use for REDIS_PASSWORD
openssl rand -base64 64  # Use for N8N_ENCRYPTION_KEY
```

#### 3.2 Environment Configuration
```bash
# Edit .env file with your configuration
nano .env
```

**Required Environment Variables**:
```bash
# Domain and SSL
DOMAIN=automation.yourdomain.com  # Or use IP address
SSL_EMAIL=admin@yourdomain.com

# Database Configuration
DB_PASSWORD=YOUR_GENERATED_DB_PASSWORD
REDIS_PASSWORD=YOUR_GENERATED_REDIS_PASSWORD

# n8n Configuration
N8N_ENCRYPTION_KEY=YOUR_GENERATED_ENCRYPTION_KEY
N8N_HOST=automation.yourdomain.com
N8N_PROTOCOL=https
N8N_PORT=443

# Webhook Configuration
WEBHOOK_URL=https://automation.yourdomain.com

# API Integration Keys (obtain from service providers)
APOLLO_API_KEY=your_apollo_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
SENDGRID_API_KEY=your_sendgrid_api_key
GHL_API_KEY=your_ghl_api_key
```

#### 3.3 Deploy with Docker Compose
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose ps

# Check logs
docker-compose logs -f
```

### Step 4: SSL Certificate Setup

#### 4.1 Let's Encrypt Configuration
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker-compose stop nginx

# Generate certificates
sudo certbot certonly --standalone \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d automation.yourdomain.com

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### 4.2 Nginx SSL Configuration
```bash
# Restart nginx with SSL
docker-compose start nginx

# Verify SSL
curl -I https://automation.yourdomain.com
```

### Step 5: n8n Workflow Import

#### 5.1 Access n8n Interface
```bash
# Navigate to your n8n installation
https://automation.yourdomain.com

# Create admin account
# Username: admin@yourdomain.com
# Password: [Use strong password]
```

#### 5.2 Import Automation Workflows
```bash
# Download workflow files
wget https://raw.githubusercontent.com/service6-automation/workflows/main/instant_lead_response.json
wget https://raw.githubusercontent.com/service6-automation/workflows/main/lead_intelligence_engine.json

# Import via n8n interface:
# 1. Go to Workflows → Import from file
# 2. Upload instant_lead_response.json
# 3. Upload lead_intelligence_engine.json
# 4. Configure credentials for each integration
```

#### 5.3 Workflow Credentials Configuration
```json
// Apollo.io Credential
{
  "name": "Apollo API",
  "type": "httpHeaderAuth",
  "data": {
    "name": "Api-Key",
    "value": "YOUR_APOLLO_API_KEY"
  }
}

// Twilio Credential
{
  "name": "Twilio SMS",
  "type": "twilioApi",
  "data": {
    "accountSid": "YOUR_TWILIO_ACCOUNT_SID",
    "authToken": "YOUR_TWILIO_AUTH_TOKEN"
  }
}

// SendGrid Credential
{
  "name": "SendGrid Email",
  "type": "sendGridApi",
  "data": {
    "apiKey": "YOUR_SENDGRID_API_KEY"
  }
}

// GoHighLevel Credential
{
  "name": "GoHighLevel CRM",
  "type": "httpHeaderAuth",
  "data": {
    "name": "Authorization",
    "value": "Bearer YOUR_GHL_API_KEY"
  }
}
```

### Step 6: Database Setup and Migration

#### 6.1 Initialize Database Schema
```bash
# Access PostgreSQL container
docker-compose exec postgres psql -U postgres -d n8n

# Run schema creation
\i /docker-entrypoint-initdb.d/schema.sql

# Verify tables created
\dt

# Exit PostgreSQL
\q
```

#### 6.2 Configure Database Backups
```bash
# Create backup script
cat > /home/service6/backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/service6/backups"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump -U postgres n8n > $BACKUP_DIR/n8n_backup_$TIMESTAMP.sql

# Backup workflows and credentials
docker cp $(docker-compose ps -q n8n):/home/node/.n8n $BACKUP_DIR/n8n_config_$TIMESTAMP

# Cleanup backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
EOF

chmod +x /home/service6/backup.sh

# Set up daily backups
echo "0 2 * * * /home/service6/backup.sh" | crontab -
```

### Step 7: Monitoring and Alerting Setup

#### 7.1 System Monitoring
```bash
# Deploy monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana dashboard
# URL: https://automation.yourdomain.com:3000
# Default login: admin/admin (change immediately)
```

#### 7.2 Health Check Endpoints
```bash
# Test system health
curl https://automation.yourdomain.com/health

# Test webhook endpoint
curl -X POST https://automation.yourdomain.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Test n8n API
curl https://automation.yourdomain.com/rest/active
```

#### 7.3 Uptime Monitoring
```bash
# Set up external monitoring (recommended services)
# - UptimeRobot (free tier available)
# - Pingdom
# - StatusCake

# Monitor these endpoints:
# https://automation.yourdomain.com/health
# https://automation.yourdomain.com/webhook/test
```

---

## API REQUIREMENTS AND SETUP

### Required Service Accounts

#### 1. Apollo.io (Lead Enrichment)
- **Plan**: Starter ($49/month) or Professional ($79/month)
- **Setup**: Create account → API Settings → Generate API key
- **Rate Limits**: 200 requests/day (Starter), 1,000/day (Professional)
- **Documentation**: https://apolloapi.com/

#### 2. Twilio (SMS Communications)
- **Plan**: Pay-as-you-go ($0.0075/SMS in US)
- **Setup**: Create account → Console → Account SID + Auth Token
- **Phone Number**: Purchase Twilio phone number ($1/month)
- **Documentation**: https://www.twilio.com/docs/

#### 3. SendGrid (Email Delivery)
- **Plan**: Free tier (100 emails/day) or Essentials ($14.95/month)
- **Setup**: Create account → Settings → API Keys
- **Domain Authentication**: Configure SPF/DKIM records
- **Documentation**: https://sendgrid.com/docs/

#### 4. GoHighLevel (CRM Integration)
- **Plan**: Existing client account required
- **Setup**: Apps → Create Private App → Generate API key
- **Permissions**: Contacts (read/write), Opportunities (read/write)
- **Documentation**: https://highlevel.stoplight.io/

### API Configuration Testing
```bash
# Test Apollo.io
curl -H "Api-Key: YOUR_APOLLO_KEY" \
  "https://api.apollo.io/v1/people/search?q=test"

# Test Twilio
curl -X POST \
  --data-urlencode "To=+1234567890" \
  --data-urlencode "From=YOUR_TWILIO_NUMBER" \
  --data-urlencode "Body=Test message" \
  -u YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN \
  https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json

# Test SendGrid
curl -X "POST" "https://api.sendgrid.com/v3/mail/send" \
  -H "Authorization: Bearer YOUR_SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"personalizations":[{"to":[{"email":"test@example.com"}]}],"from":{"email":"from@example.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'

# Test GoHighLevel
curl -H "Authorization: Bearer YOUR_GHL_API_KEY" \
  "https://services.leadconnectorhq.com/contacts/"
```

---

## SECURITY HARDENING

### Firewall Configuration
```bash
# Configure UFW (Uncomplicated Firewall)
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 3000  # Grafana (optional)

# Enable firewall
sudo ufw --force enable
sudo ufw status verbose
```

### Security Updates
```bash
# Set up automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure automatic updates
echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/20auto-upgrades
```

### SSH Hardening
```bash
# Disable root login and password authentication
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart ssh
```

### Application Security
```bash
# Set proper file permissions
sudo chown -R service6:service6 /home/service6/automation
chmod 600 /home/service6/automation/.env

# Secure database
docker-compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'NEW_STRONG_PASSWORD';"
```

---

## TESTING AND VALIDATION

### Automated Testing Suite
```bash
# Run comprehensive test suite
cd /home/service6/automation
./scripts/run_tests.sh

# Expected results:
# ✅ Webhook processing test
# ✅ Database connectivity test
# ✅ API integration tests
# ✅ Email delivery test
# ✅ SMS delivery test
# ✅ CRM synchronization test
# ✅ Lead scoring algorithm test
# ✅ Workflow execution test
```

### Load Testing
```bash
# Install artillery for load testing
npm install -g artillery

# Run load test
artillery run load_test.yml

# Expected performance:
# - 100+ concurrent webhooks processed successfully
# - <60 second response time maintained
# - <1% error rate under load
```

### End-to-End Validation
```bash
# Submit test lead through webhook
curl -X POST https://automation.yourdomain.com/webhook/lead \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "Lead",
    "phone": "+1234567890",
    "source": "website"
  }'

# Verify in logs:
# ✅ SMS sent within 30 seconds
# ✅ Email sent within 45 seconds
# ✅ CRM record created within 60 seconds
# ✅ Lead enrichment completed
# ✅ Lead score calculated
# ✅ Agent notification sent
```

---

## ONGOING MAINTENANCE

### Daily Operations
- [ ] Check system health dashboard
- [ ] Review error logs for issues
- [ ] Monitor API rate limits
- [ ] Verify backup completion

### Weekly Maintenance
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Analyze lead conversion data
- [ ] Optimize workflow performance

### Monthly Reviews
- [ ] Capacity planning assessment
- [ ] Security audit and updates
- [ ] API cost optimization
- [ ] Performance tuning

### Support Procedures
```bash
# View application logs
docker-compose logs -f n8n

# Check system resources
docker stats

# Database maintenance
docker-compose exec postgres psql -U postgres -c "VACUUM ANALYZE;"

# Restart services if needed
docker-compose restart
```

---

## TROUBLESHOOTING GUIDE

### Common Issues and Solutions

#### Issue: n8n not accessible
```bash
# Check if container is running
docker-compose ps

# Check nginx configuration
docker-compose logs nginx

# Verify SSL certificate
openssl x509 -in /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem -text -noout
```

#### Issue: Webhook not receiving requests
```bash
# Check firewall settings
sudo ufw status

# Test webhook endpoint
curl -X POST https://automation.yourdomain.com/webhook/test

# Check n8n webhook logs
docker-compose exec n8n n8n webhook --help
```

#### Issue: API integrations failing
```bash
# Test API credentials
# (Use test scripts from API Requirements section)

# Check rate limits
grep "rate.limit" docker-compose logs n8n

# Verify API endpoint configurations in n8n workflows
```

#### Issue: Database connection errors
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Test database connection
docker-compose exec postgres psql -U postgres -l

# Check database disk space
docker exec $(docker-compose ps -q postgres) df -h
```

#### Issue: Email/SMS not delivering
```bash
# Test SendGrid API key
curl -i --request POST \
--url https://api.sendgrid.com/v3/mail/send \
--header "Authorization: Bearer YOUR_API_KEY"

# Test Twilio credentials
curl -X POST \
-u YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN \
https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json
```

---

## SCALING CONSIDERATIONS

### Horizontal Scaling (High Volume)
```bash
# Load balancer configuration for multiple droplets
# Database clustering for high availability
# Redis cluster for cache scaling
# CDN integration for static assets
```

### Vertical Scaling (Performance)
```bash
# Upgrade droplet size
doctl compute droplet-action resize DROPLET_ID --size s-4vcpu-8gb --disk

# Optimize database performance
docker-compose exec postgres psql -U postgres -c "
  ALTER SYSTEM SET shared_buffers = '1GB';
  ALTER SYSTEM SET effective_cache_size = '3GB';
"
```

### Cost Optimization
- Monitor API usage and optimize calls
- Implement caching strategies
- Use reserved instances for predictable load
- Regular cleanup of old data and logs

---

## SUPPORT AND DOCUMENTATION

### Getting Help
- **Documentation**: Complete guide at docs.service6-automation.com
- **Support Email**: support@service6-automation.com
- **Community Forum**: forum.service6-automation.com
- **Video Tutorials**: youtube.com/service6automation

### Included Support (30 Days)
- Installation assistance
- Configuration troubleshooting
- Performance optimization
- Integration support
- Training sessions

### Extended Support Options
- **Monthly Support**: $99/month ongoing support
- **Priority Support**: $199/month with 4-hour response SLA
- **Managed Service**: $399/month fully managed hosting and optimization

---

**Deployment Guide Version**: 1.0
**Last Updated**: January 16, 2026
**Estimated Deployment Time**: 15-20 minutes
**Next Review**: Post-deployment optimization guide

*This deployment guide provides complete instructions for production deployment. For development or staging environments, contact support for modified configurations.*