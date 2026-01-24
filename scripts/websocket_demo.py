"""
Real-Time WebSocket Features Demonstration Script.

Demonstrates Jorge's Real Estate AI Dashboard real-time capabilities by
simulating realistic business events and showing live updates in action.

Usage:
    python scripts/websocket_demo.py --scenario=business_day
    python scripts/websocket_demo.py --scenario=high_activity
    python scripts/websocket_demo.py --scenario=performance_demo
    python scripts/websocket_demo.py --scenario=custom --events=50
"""

import asyncio
import random
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager
from ghl_real_estate_ai.services.auth_service import get_auth_service
from ghl_real_estate_ai.core.logger import get_logger

logger = get_logger(__name__)

class RealTimeDemo:
    """Real-time features demonstration orchestrator."""
    
    def __init__(self):
        self.event_publisher = get_event_publisher()
        self.websocket_manager = get_websocket_manager()
        self.auth_service = get_auth_service()
        
        # Demo data
        self.demo_leads = [
            {"name": "John Smith", "email": "john.smith@email.com", "phone": "555-0101", "budget": "500k-750k"},
            {"name": "Mary Johnson", "email": "mary.j@email.com", "phone": "555-0102", "budget": "300k-450k"},
            {"name": "Robert Davis", "email": "r.davis@email.com", "phone": "555-0103", "budget": "750k-1M"},
            {"name": "Sarah Wilson", "email": "sarah.w@email.com", "phone": "555-0104", "budget": "200k-350k"},
            {"name": "Michael Brown", "email": "m.brown@email.com", "phone": "555-0105", "budget": "450k-600k"},
            {"name": "Lisa Garcia", "email": "lisa.g@email.com", "phone": "555-0106", "budget": "600k-850k"},
            {"name": "David Miller", "email": "d.miller@email.com", "phone": "555-0107", "budget": "350k-500k"},
            {"name": "Jennifer Lee", "email": "jen.lee@email.com", "phone": "555-0108", "budget": "800k-1.2M"}
        ]
        
        self.conversation_stages = ["Q1", "Q2", "Q3", "Q4", "closing"]
        self.pipeline_statuses = ["potential", "confirmed", "paid"]
        self.lead_actions = ["created", "updated", "qualified", "hot", "contacted"]
        
        self.events_sent = 0
        
    async def run_business_day_scenario(self, duration_minutes: int = 10):
        """Simulate a typical business day with realistic event timing."""
        logger.info(f"🏢 Starting Business Day scenario ({duration_minutes} minutes)")
        
        print("\n" + "="*60)
        print("🏢 BUSINESS DAY SIMULATION")
        print("="*60)
        print("📅 Simulating a typical day in Jorge's real estate business")
        print(f"⏰ Duration: {duration_minutes} minutes (compressed time)")
        print("🔴 Watch the dashboard for live updates!")
        print("="*60)
        
        await self._initialize_services()
        
        end_time = time.time() + (duration_minutes * 60)
        hour = 9  # Start at 9 AM
        
        while time.time() < end_time:
            current_hour = hour % 24
            
            # Adjust activity based on business hours
            if 9 <= current_hour <= 17:  # Business hours
                activity_multiplier = 1.0
                interval = random.uniform(3, 8)  # 3-8 seconds between events
            elif 7 <= current_hour <= 9 or 17 <= current_hour <= 20:  # Early/late hours
                activity_multiplier = 0.5
                interval = random.uniform(8, 15)  # 8-15 seconds
            else:  # Off hours
                activity_multiplier = 0.2
                interval = random.uniform(20, 40)  # 20-40 seconds
            
            # Decide what type of event to generate
            event_type = random.choices(
                ["lead", "conversation", "commission", "performance", "system"],
                weights=[40, 30, 15, 10, 5]  # Lead events most common
            )[0]
            
            try:
                if event_type == "lead":
                    await self._generate_lead_event(current_hour)
                elif event_type == "conversation":
                    await self._generate_conversation_event(current_hour)
                elif event_type == "commission":
                    await self._generate_commission_event(current_hour)
                elif event_type == "performance":
                    await self._generate_performance_event(current_hour)
                elif event_type == "system":
                    await self._generate_system_event(current_hour)
                    
            except Exception as e:
                logger.error(f"Error generating {event_type} event: {e}")
            
            # Wait before next event
            await asyncio.sleep(interval * activity_multiplier)
            hour = (hour + random.uniform(0.1, 0.3)) % 24  # Advance time
            
        print(f"\n✅ Business Day simulation completed! Generated {self.events_sent} events")

    async def run_high_activity_scenario(self, duration_minutes: int = 5):
        """Simulate high activity period with rapid events."""
        logger.info(f"🚀 Starting High Activity scenario ({duration_minutes} minutes)")
        
        print("\n" + "="*60)
        print("🚀 HIGH ACTIVITY SIMULATION")
        print("="*60)
        print("⚡ Simulating a busy period with rapid-fire events")
        print(f"⏰ Duration: {duration_minutes} minutes")
        print("🔥 Expect frequent notifications and updates!")
        print("="*60)
        
        await self._initialize_services()
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            # Generate multiple events in quick succession
            events_batch = random.randint(2, 5)
            
            for _ in range(events_batch):
                event_type = random.choice(["lead", "conversation", "commission", "performance"])
                
                try:
                    if event_type == "lead":
                        await self._generate_lead_event(14)  # Peak hour
                    elif event_type == "conversation":
                        await self._generate_conversation_event(14)
                    elif event_type == "commission":
                        await self._generate_commission_event(14)
                    elif event_type == "performance":
                        await self._generate_performance_event(14)
                        
                except Exception as e:
                    logger.error(f"Error in high activity event: {e}")
            
            # Short pause between batches
            await asyncio.sleep(random.uniform(1, 3))
            
        print(f"\n🔥 High Activity simulation completed! Generated {self.events_sent} events")

    async def run_performance_demo(self, duration_minutes: int = 3):
        """Demonstrate system performance under load.""" 
        logger.info(f"📊 Starting Performance Demo ({duration_minutes} minutes)")
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE DEMONSTRATION")
        print("="*60)
        print("⚡ Testing system performance and WebSocket throughput")
        print(f"⏰ Duration: {duration_minutes} minutes")
        print("📈 Monitor performance metrics in real-time!")
        print("="*60)
        
        await self._initialize_services()
        
        # Performance test parameters
        events_per_second = 10
        end_time = time.time() + (duration_minutes * 60)
        
        event_count = 0
        start_time = time.time()
        
        while time.time() < end_time:
            batch_start = time.time()
            
            # Generate events batch
            for _ in range(events_per_second):
                await self._generate_performance_event(current_hour=14, include_metrics=True)
                event_count += 1
            
            # Generate periodic performance reports
            if event_count % 50 == 0:
                elapsed = time.time() - start_time
                rate = event_count / elapsed
                
                await self.event_publisher.publish_system_alert(
                    alert_type="performance_report",
                    message=f"Performance test: {event_count} events, {rate:.1f} events/sec",
                    severity="info"
                )
            
            # Maintain target rate
            batch_time = time.time() - batch_start
            target_batch_time = 1.0  # 1 second
            if batch_time < target_batch_time:
                await asyncio.sleep(target_batch_time - batch_time)
        
        final_rate = event_count / (time.time() - start_time)
        print(f"\n📊 Performance Demo completed!")
        print(f"📈 Events generated: {event_count}")
        print(f"⚡ Average rate: {final_rate:.1f} events/second")

    async def run_custom_scenario(self, total_events: int = 20, interval_seconds: float = 2.0):
        """Run custom scenario with specified parameters.""" 
        logger.info(f"🎛️ Starting Custom scenario ({total_events} events)")
        
        print("\n" + "="*60)
        print("🎛️ CUSTOM SCENARIO")
        print("="*60)
        print(f"📊 Generating {total_events} events")
        print(f"⏱️ Interval: {interval_seconds} seconds")
        print("🔄 Mixed event types for comprehensive demo")
        print("="*60)
        
        await self._initialize_services()
        
        for i in range(total_events):
            # Cycle through different event types
            event_types = ["lead", "conversation", "commission", "performance", "system"]
            event_type = event_types[i % len(event_types)]
            
            try:
                print(f"📡 Event {i+1}/{total_events}: {event_type}")
                
                if event_type == "lead":
                    await self._generate_lead_event(14)
                elif event_type == "conversation":
                    await self._generate_conversation_event(14)
                elif event_type == "commission":
                    await self._generate_commission_event(14)
                elif event_type == "performance":
                    await self._generate_performance_event(14)
                elif event_type == "system":
                    await self._generate_system_event(14)
                    
            except Exception as e:
                logger.error(f"Error in custom scenario event {i+1}: {e}")
                
            await asyncio.sleep(interval_seconds)
        
        print(f"\n🎛️ Custom scenario completed! Generated {total_events} events")

    async def _initialize_services(self):
        """Initialize required services."""
        try:
            # Initialize auth service  
            await self.auth_service.init_database()
            await self.auth_service.initialize_default_users()
            
            # Start WebSocket services
            await self.websocket_manager.start_services()
            await self.event_publisher.start()
            
            print("✅ Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise

    async def _generate_lead_event(self, current_hour: int):
        """Generate realistic lead event."""
        lead = random.choice(self.demo_leads)
        action = random.choice(self.lead_actions)
        
        # Add realistic timing-based behavior
        if 9 <= current_hour <= 12:  # Morning - more new leads
            action = random.choice(["created", "updated", "contacted"])
        elif 13 <= current_hour <= 17:  # Afternoon - more qualifications
            action = random.choice(["qualified", "hot", "updated", "contacted"])
        
        lead_id = f"LEAD_{random.randint(1000, 9999)}"
        
        # Add some realistic lead data variations
        lead_data = {
            **lead,
            "source": random.choice(["website", "referral", "facebook", "google", "zillow"]),
            "urgency": random.choice(["low", "medium", "high"]),
            "last_contact": datetime.now().isoformat()
        }
        
        if action == "qualified":
            lead_data["qualification_score"] = random.randint(70, 95)
        
        await self.event_publisher.publish_lead_update(
            lead_id=lead_id,
            lead_data=lead_data,
            action=action
        )
        
        print(f"👤 Lead {action}: {lead['name']} ({lead_id})")
        self.events_sent += 1

    async def _generate_conversation_event(self, current_hour: int):
        """Generate realistic conversation progression event."""
        conversation_id = f"CONV_{random.randint(1000, 9999)}"
        lead_id = f"LEAD_{random.randint(1000, 9999)}"
        stage = random.choice(self.conversation_stages)
        
        # Add realistic stage progression
        if random.random() < 0.7:  # 70% chance of normal progression
            if stage == "Q1":
                next_stages = ["Q2"] 
            elif stage == "Q2":
                next_stages = ["Q3", "Q1"]  # Can go back
            elif stage == "Q3":
                next_stages = ["Q4", "Q2"]  # Can go back
            elif stage == "Q4":
                next_stages = ["closing", "Q3"]  # Can go back
            else:
                next_stages = ["closing"]
                
            stage = random.choice(next_stages)
        
        # Add sample message based on stage
        stage_messages = {
            "Q1": "Thanks for your interest! Let's start with your current situation...",
            "Q2": "Great! Now let's talk about your budget and timeline...",
            "Q3": "Perfect! I have some properties that might interest you...",
            "Q4": "Excellent! Let's schedule a viewing and discuss next steps...",
            "closing": "Congratulations! Let's finalize the details..."
        }
        
        message = stage_messages.get(stage, "Let's continue our conversation...")
        
        await self.event_publisher.publish_conversation_update(
            conversation_id=conversation_id,
            lead_id=lead_id,
            stage=stage,
            message=message
        )
        
        print(f"💬 Conversation: Lead {lead_id} → {stage}")
        self.events_sent += 1

    async def _generate_commission_event(self, current_hour: int):
        """Generate realistic commission update event."""
        deal_id = f"DEAL_{random.randint(100, 999)}"
        
        # Generate realistic commission amounts
        base_amounts = [5000, 7500, 10000, 12500, 15000, 18000, 20000, 25000, 30000]
        amount = random.choice(base_amounts)
        
        # Add some variation
        amount += random.randint(-500, 1500)
        
        status = random.choice(self.pipeline_statuses)
        
        # Add realistic timing-based behavior
        if 9 <= current_hour <= 12:  # Morning - more potentials
            status = "potential"
        elif 13 <= current_hour <= 17:  # Afternoon - more confirmations/payments
            status = random.choice(["confirmed", "paid"])
        
        await self.event_publisher.publish_commission_update(
            deal_id=deal_id,
            commission_amount=float(amount),
            pipeline_status=status
        )
        
        print(f"💰 Commission: {deal_id} - ${amount:,} ({status})")
        self.events_sent += 1

    async def _generate_performance_event(self, current_hour: int, include_metrics: bool = False):
        """Generate realistic performance metric event."""
        metrics = [
            ("response_time", random.uniform(0.8, 4.2), "min"),
            ("cache_hit_rate", random.uniform(75, 95), "%"),
            ("lead_conversion_rate", random.uniform(12, 28), "%"),
            ("api_response_time", random.uniform(150, 800), "ms"),
            ("websocket_connections", random.randint(5, 50), ""),
            ("events_per_minute", random.randint(8, 45), ""),
            ("database_queries_per_sec", random.uniform(10, 100), "")
        ]
        
        metric_name, metric_value, unit = random.choice(metrics)
        
        # Add comparison data for trends
        previous_value = metric_value * random.uniform(0.85, 1.15)
        comparison = {
            "previous_value": previous_value,
            "current_value": metric_value,
            "change_percent": ((metric_value - previous_value) / previous_value) * 100
        }
        
        await self.event_publisher.publish_performance_update(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=unit,
            comparison=comparison
        )
        
        if include_metrics:
            trend = "↗️" if metric_value > previous_value else "↘️" if metric_value < previous_value else "→"
            print(f"📊 Performance: {metric_name} = {metric_value:.1f}{unit} {trend}")
        
        self.events_sent += 1

    async def _generate_system_event(self, current_hour: int):
        """Generate realistic system alert event."""
        alert_types = [
            ("performance_optimization", "Cache optimization completed", "info"),
            ("backup_completed", "Daily backup completed successfully", "info"),
            ("high_load", "High server load detected", "warning"),
            ("maintenance_scheduled", "Maintenance scheduled for tonight", "info"),
            ("integration_health", "GHL API connection healthy", "info"),
            ("security_scan", "Security scan completed - no issues", "info"),
            ("database_optimization", "Database optimization in progress", "info")
        ]
        
        alert_type, message, severity = random.choice(alert_types)
        
        # Add some realistic details
        details = {
            "timestamp": datetime.now().isoformat(),
            "server": f"server-{random.randint(1, 5)}",
            "component": random.choice(["websocket", "api", "database", "cache", "frontend"])
        }
        
        await self.event_publisher.publish_system_alert(
            alert_type=alert_type,
            message=message,
            severity=severity,
            details=details
        )
        
        severity_icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
        icon = severity_icons.get(severity, "ℹ️")
        print(f"{icon} System: {alert_type} - {message}")
        self.events_sent += 1

async def main():
    """Main demo runner."""
    parser = argparse.ArgumentParser(description='Real-Time WebSocket Features Demo')
    parser.add_argument('--scenario', choices=['business_day', 'high_activity', 'performance_demo', 'custom'],
                       default='business_day', help='Demo scenario to run')
    parser.add_argument('--duration', type=int, default=10,
                       help='Duration in minutes for time-based scenarios')
    parser.add_argument('--events', type=int, default=20,
                       help='Number of events for custom scenario')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='Interval between events in seconds for custom scenario')
    
    args = parser.parse_args()
    
    print("🎭 Jorge's Real Estate AI Dashboard - Real-Time Features Demo")
    print(f"📅 Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    demo = RealTimeDemo()
    
    try:
        if args.scenario == 'business_day':
            await demo.run_business_day_scenario(args.duration)
        elif args.scenario == 'high_activity':
            await demo.run_high_activity_scenario(args.duration)
        elif args.scenario == 'performance_demo':
            await demo.run_performance_demo(args.duration)
        elif args.scenario == 'custom':
            await demo.run_custom_scenario(args.events, args.interval)
            
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo execution error")
        return 1
    
    print("\n🎉 Demo completed successfully!")
    print("👀 Check your dashboard to see all the real-time updates!")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))