# Sponsors Section Template

Use this template to add a sponsors recognition section to your README.md or project documentation.

---

## Markdown Template

```markdown
---

## ❤️ Sponsors

EnterpriseHub is supported by amazing sponsors. Thank you for helping build the future of AI-powered real estate!

### Enterprise Sponsors

| Sponsor | Since | Website |
|---------|-------|---------|
| [Your Company Name](https://yourcompany.com) | February 2026 | Real Estate CRM Solutions |

### Builder Sponsors

| Sponsor | Since | GitHub |
|---------|-------|--------|
| [@username](https://github.com/username) | February 2026 | Building RAG integrations |

### Supporters

| Sponsor | Since |
|---------|-------|
| [@username1](https://github.com/username1) | February 2026 |
| [@username2](https://github.com/username2) | February 2026 |
| [@username3](https://github.com/username3) | February 2026 |

---

### Become a Sponsor

Support EnterpriseHub development and get exclusive benefits:

| Tier | Price | Benefits |
|------|-------|----------|
| **Supporter** | $5/mo | Name in README, sponsor badge |
| **Builder** | $15/mo | 24h issue responses, Builder badge, quarterly calls |
| **Enterprise** | $50/mo | Monthly calls, dedicated Slack, enterprise badge |

👉 [Sponsor via GitHub Sponsors](https://github.com/sponsors/ChunkyTortoise)

```

---

## HTML Template (for websites)

```html
<section id="sponsors" class="sponsors-section">
    <h2>❤️ Sponsors</h2>
    <p>EnterpriseHub is supported by amazing sponsors. Thank you for helping build the future of AI-powered real estate!</p>
    
    <div class="sponsor-tiers">
        <!-- Enterprise Sponsors -->
        <div class="sponsor-tier enterprise">
            <h3>Enterprise Sponsors</h3>
            <div class="sponsor-grid">
                <a href="https://yourcompany.com" target="_blank" class="sponsor-card">
                    <div class="sponsor-logo">
                        <img src="/assets/sponsors/your-company.png" alt="Your Company">
                    </div>
                    <span class="sponsor-name">Your Company</span>
                    <span class="sponsor-badge enterprise-badge">Enterprise</span>
                </a>
            </div>
        </div>
        
        <!-- Builder Sponsors -->
        <div class="sponsor-tier builder">
            <h3>Builder Sponsors</h3>
            <div class="sponsor-grid">
                <a href="https://github.com/username" target="_blank" class="sponsor-card">
                    <img src="https://github.com/username.png?size=64" alt="@username" class="sponsor-avatar">
                    <span class="sponsor-name">@username</span>
                    <span class="sponsor-badge builder-badge">Builder</span>
                </a>
            </div>
        </div>
        
        <!-- Supporters -->
        <div class="sponsor-tier supporters">
            <h3>Supporters</h3>
            <div class="supporter-avatars">
                <a href="https://github.com/user1" target="_blank">
                    <img src="https://github.com/user1.png?size=48" alt="@user1" title="@user1">
                </a>
                <a href="https://github.com/user2" target="_blank">
                    <img src="https://github.com/user2.png?size=48" alt="@user2" title="@user2">
                </a>
                <a href="https://github.com/user3" target="_blank">
                    <img src="https://github.com/user3.png?size=48" alt="@user3" title="@user3">
                </a>
            </div>
        </div>
    </div>
    
    <div class="cta-section">
        <h3>Become a Sponsor</h3>
        <p>Support EnterpriseHub development and get exclusive benefits.</p>
        <a href="https://github.com/sponsors/ChunkyTortoise" class="sponsor-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            Sponsor via GitHub
        </a>
    </div>
</section>
```

---

## CSS Styles (for HTML template)

```css
.sponsors-section {
    padding: 2rem 0;
    border-top: 1px solid #e1e4e8;
    margin-top: 2rem;
}

.sponsor-tier {
    margin: 1.5rem 0;
}

.sponsor-tier h3 {
    font-size: 1rem;
    color: #586069;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.sponsor-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.sponsor-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    text-decoration: none;
    color: #24292e;
    transition: border-color 0.2s;
}

.sponsor-card:hover {
    border-color: #0366d6;
}

.sponsor-avatar {
    border-radius: 50%;
    width: 48px;
    height: 48px;
}

.sponsor-name {
    font-weight: 600;
}

.sponsor-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
    font-weight: 500;
}

.enterprise-badge {
    background: #ffd700;
    color: #24292e;
}

.builder-badge {
    background: #6f42c1;
    color: white;
}

.supporter-avatars {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.supporter-avatars a {
    transition: transform 0.2s;
}

.supporter-avatars a:hover {
    transform: scale(1.1);
}

.supporter-avatars img {
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.cta-section {
    margin-top: 2rem;
    text-align: center;
    padding: 2rem;
    background: #f6f8fa;
    border-radius: 8px;
}

.sponsor-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #238636;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    transition: background 0.2s;
}

.sponsor-btn:hover {
    background: #2ea043;
}
```

---

## Badge Placement Guidelines

### GitHub Profile Badge

GitHub Sponsors automatically displays badges on sponsor profiles. The tier is shown:

- ⭐ **Supporter** - Star icon
- 🛠️ **Builder** - Hammer/wrench icon  
- 🏢 **Enterprise** - Building icon

### README Placement

Recommended order in README.md:

1. After the "Features" or "Architecture" section
2. Before "Getting Started" or "Installation"
3. Alternatively, at the very end of the README

---

## Sponsor Recognition Examples

### Simple (Supporter tier)

```markdown
---

## ❤️ Thanks to Our Supporters

[@user1](https://github.com/user1), [@user2](https://github.com/user2), and [@user3](https://github.com/user3) for your support!

[Sponsor us →](https://github.com/sponsors/ChunkyTortoise)
```

### Detailed (All tiers)

See the markdown template above for comprehensive sponsor recognition.

---

*Last updated: February 2026*
