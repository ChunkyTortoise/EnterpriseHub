"""
Seed script to migrate hardcoded templates to the Template Library Service.
"""

import asyncio
from ghl_real_estate_ai.services.template_library_service import get_template_library_service, TemplateType, TemplateStatus

async def seed_templates():
    service = await get_template_library_service()
    
    # Twilio SMS Templates
    sms_templates = [
        {
            "name": "SMS: Instant Response",
            "description": "Immediate response to new lead interest",
            "type": TemplateType.SMS,
            "status": TemplateStatus.ACTIVE,
            "content": "Hi {{first_name}}! Thanks for your interest. I'm {{agent_name}} and I'll be helping you. What's the best time to chat? Reply STOP to opt out.",
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True}
            ]
        },
        {
            "name": "SMS: Follow-up 24h",
            "description": "24-hour follow-up message",
            "type": TemplateType.SMS,
            "status": TemplateStatus.ACTIVE,
            "content": "Hi {{first_name}}, just checking in! Did you have a chance to review the information I sent? Any questions? - {{agent_name}}",
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True}
            ]
        },
        {
            "name": "SMS: Follow-up 48h",
            "description": "48-hour follow-up message",
            "type": TemplateType.SMS,
            "status": TemplateStatus.ACTIVE,
            "content": "{{first_name}}, I have some great options that match your criteria. When would be a good time for a quick 10-min call? - {{agent_name}}",
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True}
            ]
        },
        {
            "name": "SMS: Follow-up 72h",
            "description": "72-hour follow-up message",
            "type": TemplateType.SMS,
            "status": TemplateStatus.ACTIVE,
            "content": "Hi {{first_name}}, I don't want you to miss out on the current market opportunities. Are you still looking? Let me know! - {{agent_name}}",
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True}
            ]
        },
        {
            "name": "SMS: Appointment Reminder",
            "description": "Reminder for upcoming appointment",
            "type": TemplateType.SMS,
            "status": TemplateStatus.ACTIVE,
            "content": "Hi {{first_name}}, this is a reminder about our call tomorrow at {{time}}. Looking forward to speaking with you! - {{agent_name}}",
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "time", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True}
            ]
        },
        {
            "name": "SMS: Hot Lead Alert",
            "description": "Urgent alert for highly active leads",
            "type": TemplateType.SMS,
            "status": TemplateStatus.ACTIVE,
            "content": "Hi {{first_name}}! I see you're actively looking. I have some exclusive listings that aren't public yet. Can we chat today? - {{agent_name}}",
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True}
            ]
        }
    ]
    
    # SendGrid Email Templates
    email_templates = [
        {
            "name": "Email: Welcome",
            "description": "Welcome email for new leads",
            "type": TemplateType.EMAIL,
            "status": TemplateStatus.ACTIVE,
            "subject": "Welcome {{first_name}}! Let's find your perfect property",
            "content": """
            <html>
            <body>
                <h2>Hi {{first_name}}!</h2>
                <p>Thank you for reaching out about real estate opportunities. I'm {{agent_name}} and I'm excited to help you find the perfect property.</p>
                <p>Based on your interest, I'll be sending you:</p>
                <ul>
                    <li>Exclusive listings that match your criteria</li>
                    <li>Market insights and trends</li>
                    <li>Tips for buyers in today's market</li>
                </ul>
                <p>What's the best way to reach you? I'd love to schedule a quick 15-minute call to understand your needs better.</p>
                <p>Best regards,<br>{{agent_name}}<br>{{agent_phone}}</p>
            </body>
            </html>
            """,
            "variables": [
                {"name": "first_name", "type": "string", "required": True},
                {"name": "agent_name", "type": "string", "required": True},
                {"name": "agent_phone", "type": "string", "required": True}
            ]
        }
    ]
    
    print(f"Seeding {len(sms_templates)} SMS templates...")
    for t in sms_templates:
        try:
            await service.create_template(t, created_by="system-seed")
            print(f"  - Created {t['name']}")
        except Exception as e:
            print(f"  - Failed to create {t['name']}: {e}")
            
    print(f"Seeding {len(email_templates)} Email templates...")
    for t in email_templates:
        try:
            await service.create_template(t, created_by="system-seed")
            print(f"  - Created {t['name']}")
        except Exception as e:
            print(f"  - Failed to create {t['name']}: {e}")

if __name__ == "__main__":
    asyncio.run(seed_templates())
