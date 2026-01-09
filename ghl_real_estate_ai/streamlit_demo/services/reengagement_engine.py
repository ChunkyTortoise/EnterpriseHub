"""
Re-engagement Engine for Silent Leads.

Automatically detects and re-engages leads who go silent after initial contact.

Features:
- Time-based trigger detection (24h, 48h, 72h)
- SMS-compliant message templates (Jorge's direct tone)
- Integration with GHL client for sending
- Memory service integration for tracking
- Prevents duplicate re-engagement attempts

Usage:
    engine = ReengagementEngine()
    silent_leads = await engine.scan_for_silent_leads()
    for lead in silent_leads:
        await engine.send_reengagement_message(
            contact_id=lead["contact_id"],
            contact_name=lead["contact_name"],
            context=lead["context"]
        )
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json

# Local imports (avoid circular dependencies)
try:
    from services.ghl_client import GHLClient
    from services.memory_service import MemoryService
except ImportError:
    # Fallback - these services optional for demo mode
    GHLClient = None
    MemoryService = None

import logging
logger = logging.getLogger(__name__)

# Mock MessageType enum
from enum import Enum
class MessageType(str, Enum):
    SMS = "SMS"
    EMAIL = "Email"
    WHATSAPP = "WhatsApp"

def get_reengagement_message(trigger_type: str, lead_context: dict) -> str:
    """Fallback message template generator"""
    return f"Hi {lead_context.get('name', 'there')}! Just wanted to check in..."


class ReengagementTrigger(Enum):
    """Re-engagement trigger levels based on time elapsed."""
    HOURS_24 = "24h"
    HOURS_48 = "48h"
    HOURS_72 = "72h"


class ReengagementEngine:
    """
    Engine for detecting and re-engaging silent leads.

    Monitors conversation history and triggers automated re-engagement
    messages at 24h, 48h, and 72h intervals.
    """

    def __init__(
        self,
        ghl_client: Optional[GHLClient] = None,
        memory_service: Optional[MemoryService] = None
    ):
        """
        Initialize re-engagement engine.

        Args:
            ghl_client: GHL API client (creates new if not provided)
            memory_service: Memory service for tracking conversations
        """
        self.ghl_client = ghl_client or GHLClient()
        self.memory_service = memory_service or MemoryService(storage_type="file")

    async def detect_trigger(self, context: Dict[str, Any]) -> Optional[ReengagementTrigger]:
        """
        Detect if a lead needs re-engagement based on time elapsed.

        Args:
            context: Conversation context from memory service

        Returns:
            ReengagementTrigger if action needed, None otherwise

        Logic:
            - 24-48h: Send first re-engagement (24h)
            - 48-72h: Send second re-engagement (48h)
            - 72h+: Send final re-engagement (72h)
            - Already sent same trigger: Skip to prevent duplicates
        """
        # Get last interaction timestamp
        last_interaction_str = context.get("last_interaction_at")
        if not last_interaction_str:
            logger.warning(f"No last_interaction_at for contact {context.get('contact_id')}")
            return None

        try:
            last_interaction = datetime.fromisoformat(last_interaction_str)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp format: {last_interaction_str}, error: {e}")
            return None

        # Calculate hours since last interaction
        now = datetime.utcnow()
        hours_elapsed = (now - last_interaction).total_seconds() / 3600

        # Get last re-engagement trigger (if any) to prevent duplicates
        last_trigger = context.get("last_reengagement_trigger")

        # Determine trigger level
        if hours_elapsed >= 72:
            # 72h+ trigger (final attempt)
            if last_trigger == ReengagementTrigger.HOURS_72.value:
                logger.info(f"72h trigger already sent for {context.get('contact_id')}")
                return None
            return ReengagementTrigger.HOURS_72

        elif hours_elapsed >= 48:
            # 48-72h trigger
            if last_trigger in [ReengagementTrigger.HOURS_48.value, ReengagementTrigger.HOURS_72.value]:
                logger.info(f"48h trigger already sent for {context.get('contact_id')}")
                return None
            return ReengagementTrigger.HOURS_48

        elif hours_elapsed >= 24:
            # 24-48h trigger
            if last_trigger:
                # Already sent any re-engagement, skip 24h
                logger.info(f"24h trigger already sent for {context.get('contact_id')}")
                return None
            return ReengagementTrigger.HOURS_24

        else:
            # Less than 24h, no trigger
            return None

    def get_message_for_trigger(
        self,
        trigger: ReengagementTrigger,
        contact_name: str,
        action: Optional[str] = None,
        is_buyer: Optional[bool] = None,
        is_seller: Optional[bool] = None
    ) -> str:
        """
        Get re-engagement message for specific trigger.

        Args:
            trigger: Trigger level (24h, 48h, 72h)
            contact_name: Lead's first name
            action: Action verb (e.g., "buy", "sell")
            is_buyer: True if lead is buying
            is_seller: True if lead is selling

        Returns:
            SMS-compliant re-engagement message (<160 chars)
        """
        return get_reengagement_message(
            trigger_level=trigger.value,
            contact_name=contact_name,
            action=action,
            is_buyer=is_buyer,
            is_seller=is_seller
        )

    def _determine_lead_goal(self, context: Dict[str, Any]) -> tuple[Optional[str], Optional[bool], Optional[bool]]:
        """
        Determine lead's goal (buy/sell) from context.

        Args:
            context: Conversation context

        Returns:
            Tuple of (action, is_buyer, is_seller)
        """
        preferences = context.get("extracted_preferences", {})
        goal = preferences.get("goal", "").lower()

        if "buy" in goal:
            return "buy", True, False
        elif "sell" in goal:
            return "sell", False, True
        else:
            # Try to infer from conversation history
            history = context.get("conversation_history", [])
            for msg in history:
                content = msg.get("content", "").lower()
                if any(word in content for word in ["buy", "buying", "purchase"]):
                    return "buy", True, False
                elif any(word in content for word in ["sell", "selling", "list"]):
                    return "sell", False, True

        # Default to general
        return None, None, None

    async def send_reengagement_message(
        self,
        contact_id: str,
        contact_name: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send re-engagement message to a silent lead.

        Args:
            contact_id: GHL contact ID
            contact_name: Lead's first name
            context: Conversation context

        Returns:
            GHL API response if sent, None if no trigger detected
        """
        # Detect trigger
        trigger = await self.detect_trigger(context)
        if not trigger:
            logger.info(f"No re-engagement trigger for {contact_id}")
            return None

        # Determine lead goal
        action, is_buyer, is_seller = self._determine_lead_goal(context)

        # Get appropriate message
        message = self.get_message_for_trigger(
            trigger=trigger,
            contact_name=contact_name,
            action=action,
            is_buyer=is_buyer,
            is_seller=is_seller
        )

        logger.info(
            f"Sending {trigger.value} re-engagement to {contact_id}: {message}",
            extra={"contact_id": contact_id, "trigger": trigger.value}
        )

        # Send via GHL
        try:
            result = await self.ghl_client.send_message(
                contact_id=contact_id,
                message=message,
                channel=MessageType.SMS
            )

            # Update context to track re-engagement
            context["last_reengagement_trigger"] = trigger.value
            context["last_reengagement_at"] = datetime.utcnow().isoformat()

            # Save updated context
            await self.memory_service.save_context(
                contact_id=contact_id,
                context=context,
                location_id=context.get("location_id")
            )

            logger.info(
                f"Successfully sent {trigger.value} re-engagement to {contact_id}",
                extra={"contact_id": contact_id, "trigger": trigger.value, "message_id": result.get("messageId")}
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to send re-engagement to {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)}
            )
            return None

    async def scan_for_silent_leads(
        self,
        memory_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan memory service for silent leads that need re-engagement.

        Args:
            memory_dir: Directory to scan (defaults to data/memory)

        Returns:
            List of silent lead dicts with contact_id, context, and trigger
        """
        if memory_dir is None:
            memory_dir = Path("data/memory")

        if not memory_dir.exists():
            logger.warning(f"Memory directory does not exist: {memory_dir}")
            return []

        silent_leads = []

        # Scan all memory files
        for file_path in memory_dir.glob("**/*.json"):
            try:
                with open(file_path, "r") as f:
                    context = json.load(f)

                contact_id = context.get("contact_id")
                if not contact_id:
                    continue

                # Check if trigger detected
                trigger = await self.detect_trigger(context)
                if trigger:
                    # Extract contact name from context or conversation
                    contact_name = self._extract_contact_name(context)

                    silent_leads.append({
                        "contact_id": contact_id,
                        "contact_name": contact_name,
                        "context": context,
                        "trigger": trigger,
                        "hours_since_interaction": self._calculate_hours_since(context)
                    })

            except Exception as e:
                logger.error(f"Error scanning {file_path}: {str(e)}")
                continue

        logger.info(f"Scanned {memory_dir}, found {len(silent_leads)} silent leads")

        return silent_leads

    def _extract_contact_name(self, context: Dict[str, Any]) -> str:
        """Extract contact name from context or default to 'there'."""
        # Try extracted preferences first
        preferences = context.get("extracted_preferences", {})
        if "name" in preferences:
            return preferences["name"]

        # Try conversation history
        history = context.get("conversation_history", [])
        for msg in history:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Simple name extraction: "my name is X"
                if "name is" in content.lower():
                    parts = content.lower().split("name is")
                    if len(parts) > 1:
                        name_candidate = parts[1].strip().split()[0]
                        return name_candidate.capitalize()

        # Default
        return "there"

    def _calculate_hours_since(self, context: Dict[str, Any]) -> float:
        """Calculate hours since last interaction."""
        last_interaction_str = context.get("last_interaction_at")
        if not last_interaction_str:
            return 0.0

        try:
            last_interaction = datetime.fromisoformat(last_interaction_str)
            now = datetime.utcnow()
            return (now - last_interaction).total_seconds() / 3600
        except (ValueError, TypeError):
            return 0.0

    async def process_all_silent_leads(
        self,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Process all silent leads and send re-engagement messages.

        Args:
            dry_run: If True, only detect but don't send messages

        Returns:
            Summary dict with counts and results
        """
        silent_leads = await self.scan_for_silent_leads()

        summary = {
            "total_scanned": len(silent_leads),
            "messages_sent": 0,
            "errors": 0,
            "dry_run": dry_run,
            "results": []
        }

        for lead in silent_leads:
            contact_id = lead["contact_id"]
            contact_name = lead["contact_name"]
            context = lead["context"]
            trigger = lead["trigger"]

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would send {trigger.value} to {contact_id} ({contact_name})",
                    extra={"contact_id": contact_id, "trigger": trigger.value}
                )
                summary["results"].append({
                    "contact_id": contact_id,
                    "trigger": trigger.value,
                    "status": "dry_run"
                })
            else:
                result = await self.send_reengagement_message(
                    contact_id=contact_id,
                    contact_name=contact_name,
                    context=context
                )

                if result:
                    summary["messages_sent"] += 1
                    summary["results"].append({
                        "contact_id": contact_id,
                        "trigger": trigger.value,
                        "status": "sent",
                        "message_id": result.get("messageId")
                    })
                else:
                    summary["errors"] += 1
                    summary["results"].append({
                        "contact_id": contact_id,
                        "trigger": trigger.value,
                        "status": "error"
                    })

        logger.info(
            f"Re-engagement batch complete: {summary['messages_sent']} sent, {summary['errors']} errors",
            extra=summary
        )

        return summary


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

async def main():
    """CLI interface for testing re-engagement engine."""
    import sys

    engine = ReengagementEngine()

    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        print("Scanning for silent leads...")
        silent_leads = await engine.scan_for_silent_leads()
        print(f"\nFound {len(silent_leads)} silent leads:")

        for lead in silent_leads:
            print(f"\n  Contact ID: {lead['contact_id']}")
            print(f"  Name: {lead['contact_name']}")
            print(f"  Trigger: {lead['trigger'].value}")
            print(f"  Hours since interaction: {lead['hours_since_interaction']:.1f}h")

    elif len(sys.argv) > 1 and sys.argv[1] == "process":
        dry_run = "--dry-run" in sys.argv
        print(f"Processing silent leads (dry_run={dry_run})...")

        summary = await engine.process_all_silent_leads(dry_run=dry_run)

        print(f"\nSummary:")
        print(f"  Total scanned: {summary['total_scanned']}")
        print(f"  Messages sent: {summary['messages_sent']}")
        print(f"  Errors: {summary['errors']}")

    else:
        print("Usage:")
        print("  python services/reengagement_engine.py scan")
        print("  python services/reengagement_engine.py process [--dry-run]")


if __name__ == "__main__":
    asyncio.run(main())
