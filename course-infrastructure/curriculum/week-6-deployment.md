# Week 6: Deployment + Operations (Student Project)

## Overview

The final week. Students deploy their own AI project with Docker, CI/CD, monitoring, and Stripe billing. By Thursday, every student has a live, deployed product.

**Repo**: Student's own project (built over previous 5 weeks)
**Lab**: Deploy with Docker + CI/CD + monitoring + Stripe

## Learning Objectives

By the end of this week, students will be able to:
1. Containerize a Python AI application with multi-stage Docker builds
2. Set up CI/CD with GitHub Actions including quality gates
3. Configure health checks, monitoring, and alerting for deployed services
4. Integrate Stripe Checkout for subscription billing
5. Present their deployed product in a 5-minute demo

## Session A: Concepts + Live Coding (Tuesday)

### Part 1: Deployment Architecture (15 min)

**Production deployment stack:**
```
User → CDN/Load Balancer → Application Container → Database + Cache
                              ↓
                         CI/CD Pipeline
                              ↓
                     GitHub → Build → Test → Deploy
```

**Deployment targets:**
- Render: Easy, good free tier, auto-deploy from GitHub
- Railway: Similar to Render, good for databases
- Fly.io: Edge deployment, good for latency-sensitive apps
- AWS/GCP: Full control, more complex, enterprise-scale

For this course: Render (simplest path to a live URL).

### Part 2: Live Coding — Full Deployment (45 min)

1. **Docker containerization** (15 min)
   - Multi-stage Dockerfile: build stage + runtime stage
   - Python-specific: slim base image, pip install from requirements
   - Health check endpoint: `/health` returns service status
   - Environment variables: never bake secrets into images
   - docker-compose for local development (app + postgres + redis)

   ```dockerfile
   # Build stage
   FROM python:3.11-slim AS builder
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Runtime stage
   FROM python:3.11-slim
   WORKDIR /app
   COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
   COPY . .
   EXPOSE 8000
   HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **GitHub Actions CI/CD** (15 min)
   - Workflow file: `.github/workflows/deploy.yml`
   - Steps: checkout → setup Python → install deps → lint → test → deploy
   - Quality gates: tests must pass, linting must pass, no security vulnerabilities
   - Deploy on push to main only
   - Secrets management: GitHub Secrets for API keys

3. **Stripe integration** (15 min)
   - Create products and prices in Stripe Dashboard
   - Checkout Sessions API: redirect user to Stripe-hosted checkout
   - Webhook handler: `checkout.session.completed` event
   - Subscription management: create, update, cancel
   - Test mode: use test API keys, test card numbers

### Part 3: Lab Introduction (15 min)

- Lab 6: Deploy YOUR project (not a pre-built starter)
- Choose your best work from Weeks 1-5 (or combine multiple)
- Autograder checks: live URL responds, health check passes, CI/CD pipeline green
- Bonus: Stripe test checkout completes successfully

### Part 4: Q&A (15 min)

## Session B: Final Presentations + Wrap-up (Thursday)

### Part 1: Lab 6 Solution Review (20 min)

Common deployment issues:
- Environment variables not set in production
- Database connection string using localhost instead of service name
- Missing health check endpoint
- CI/CD pipeline passing but deployment failing (build vs runtime errors)

### Part 2: Student Presentations (60 min)

Each student presents their deployed project (5 minutes each):

**Presentation format:**
1. What you built (30 seconds)
2. Live demo — show the deployed URL working (2 minutes)
3. Architecture diagram (1 minute)
4. One thing you learned that surprised you (30 seconds)
5. What you'd add next (30 seconds)

**Audience participation:**
- Each student asks one question to at least one presenter
- Instructor provides brief feedback after each presentation
- Class votes for "Most Production-Ready" and "Most Creative" awards

### Part 3: Course Retrospective (10 min)

- What went well? What could be improved?
- Anonymous feedback form (shared via Discord)
- NPS survey
- Certificate distribution (Certifier links sent via email)

### Part 4: What's Next (10 min)

**For your career:**
- Add all 5 projects to your portfolio/resume
- Write a LinkedIn post about what you built (use social templates)
- Update your GitHub profile with pinned repositories

**For your skills:**
- Explore the full production repos beyond the lab scope
- Contribute to the open-source repos (issues labeled "good first issue")
- Join the alumni Discord for ongoing learning and networking

**For revenue:**
- Deploy your projects as SaaS products
- Offer AI consulting services using your portfolio as proof of capability
- Consider the self-paced version as a teaching resource for your team

**Upcoming:**
- Alumni office hours (quarterly)
- Cohort 2 TA opportunities (paid)
- Guest speaker invitations for future cohorts

## Key Takeaways

1. Docker containerization makes deployments reproducible
2. CI/CD with quality gates catches bugs before they reach production
3. Health checks and monitoring are not optional for production services
4. Stripe Checkout is the fastest path to accepting payments
5. A deployed product in your portfolio is worth 100 tutorials

## Resources

- Docker documentation (multi-stage builds)
- GitHub Actions documentation
- Render deployment guide
- Stripe Checkout documentation
- Course certificate: issued via Certifier within 48 hours of completion
