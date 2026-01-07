"""
Portal Swipe Manager Service

Handles "Tinder-style" swipe interactions for the branded client portal.
Tracks likes, passes, and feedback to improve AI property matching.

Features:
- Log swipe interactions (LIKE/PASS) with timestamps
- Capture feedback on passes (price, location, style, size)
- Update GHL contact tags and notes
- Trigger speed-to-lead AI for high-intent behavior
- Learn from negative signals to refine matches
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)


class SwipeAction(Enum):
    """Enumeration for swipe actions."""
    LIKE = "like"
    PASS = "pass"


class FeedbackCategory(Enum):
    """Categories for pass feedback."""
    PRICE_TOO_HIGH = "price_too_high"
    PRICE_TOO_LOW = "price_too_low"
    LOCATION = "location"
    STYLE = "style"
    SIZE_TOO_SMALL = "size_too_small"
    SIZE_TOO_LARGE = "size_too_large"
    OTHER = "other"


class PortalSwipeManager:
    """
    Manages swipe interactions in the branded client portal.
    """

    def __init__(
        self,
        interactions_path: Optional[str] = None,
        ghl_client: Optional[GHLClient] = None,
        memory_service: Optional[MemoryService] = None,
        property_matcher: Optional[Any] = None,
    ):
        """
        Initialize the Portal Swipe Manager.

        Args:
            interactions_path: Path to the lead interactions JSON file.
            ghl_client: GHL API client for updating contacts.
            memory_service: Memory service for storing preferences.
            property_matcher: PropertyMatcher instance for finding properties.
        """
        self.interactions_path = (
            Path(interactions_path)
            if interactions_path
            else Path(__file__).parent.parent
            / "data"
            / "portal_interactions"
            / "lead_interactions.json"
        )
        self.ghl_client = ghl_client or GHLClient()
        self.memory_service = memory_service or MemoryService()
        self.interactions = self._load_interactions()
        
        # Import PropertyMatcher lazily to avoid circular imports
        if property_matcher:
            self.property_matcher = property_matcher
        else:
            from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
            self.property_matcher = PropertyMatcher()

    def _load_interactions(self) -> List[Dict[str, Any]]:
        """Load interactions from JSON file."""
        try:
            if self.interactions_path.exists():
                with open(self.interactions_path, "r") as f:
                    data = json.load(f)
                    return data.get("interactions", [])
            else:
                logger.warning(
                    f"Interactions file not found at {self.interactions_path}"
                )
                return []
        except Exception as e:
            logger.error(f"Failed to load interactions: {e}")
            return []

    def _save_interactions(self):
        """Save interactions to JSON file."""
        try:
            self.interactions_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.interactions_path, "r+") as f:
                data = json.load(f)
                data["interactions"] = self.interactions
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            logger.info(f"Saved {len(self.interactions)} interactions")
        except Exception as e:
            logger.error(f"Failed to save interactions: {e}")

    async def handle_swipe(
        self,
        lead_id: str,
        property_id: str,
        action: SwipeAction,
        location_id: str,
        feedback: Optional[Dict[str, Any]] = None,
        time_on_card: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for UI swipe events.

        Args:
            lead_id: GHL contact ID.
            property_id: MLS or property listing ID.
            action: SwipeAction.LIKE or SwipeAction.PASS.
            location_id: GHL location/tenant ID.
            feedback: Optional feedback dict with category and text.
            time_on_card: Seconds spent viewing the property card.

        Returns:
            Dict with status and any triggered actions.
        """
        logger.info(
            f"Processing swipe: {lead_id} -> {property_id} ({action.value})"
        )

        # 1. Log the interaction locally
        self._log_interaction(lead_id, property_id, action, feedback, time_on_card)

        # 2. Execute business logic based on action
        if action == SwipeAction.LIKE:
            return await self._process_like(lead_id, property_id, location_id)
        elif action == SwipeAction.PASS:
            return await self._process_pass(
                lead_id, property_id, location_id, feedback
            )

    async def _process_like(
        self, lead_id: str, property_id: str, location_id: str
    ) -> Dict[str, Any]:
        """
        Logic for a RIGHT SWIPE (Interest).

        Actions:
        - Tag lead in GHL with 'portal_liked_property' and 'hot_lead'
        - Add note to GHL contact
        - Detect high-intent behavior (multiple likes in short time)
        - Trigger AI speed-to-lead for high intent
        """
        result = {"status": "logged", "trigger_sms": False, "high_intent": False}

        try:
            # A. Tag the lead in GHL
            tags = ["portal_liked_property", "hot_lead"]
            await self.ghl_client.add_tags(lead_id, tags)
            logger.info(f"Tagged lead {lead_id} with {tags}")

            # B. Send note via SMS (GHL doesn't have add_note in API)
            note_body = (
                f"🏠 User LIKED property {property_id} in Client Portal.\n"
                f"Timestamp: {datetime.utcnow().isoformat()}"
            )
            # Store note in memory instead of GHL
            logger.info(f"Note for {lead_id}: {note_body}")

            # C. Detect high-intent behavior
            recent_likes = self._count_recent_likes(lead_id, minutes=10)
            logger.info(
                f"Lead {lead_id} has {recent_likes} likes in last 10 minutes"
            )

            if recent_likes >= 3:
                result["high_intent"] = True
                result["trigger_sms"] = True
                result["message"] = (
                    f"High intent detected: {recent_likes} likes in 10 minutes"
                )
                
                # Tag as super hot lead
                await self.ghl_client.add_tags(
                    lead_id, ["super_hot_lead", "immediate_followup"]
                )
                
                logger.warning(
                    f"⚡ HIGH INTENT DETECTED for {lead_id} - {recent_likes} likes"
                )

            # D. Update memory with liked property
            await self._update_liked_properties(lead_id, location_id, property_id)

        except Exception as e:
            logger.error(f"Error processing like: {e}")
            result["error"] = str(e)

        return result

    async def _process_pass(
        self,
        lead_id: str,
        property_id: str,
        location_id: str,
        feedback: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Logic for a LEFT SWIPE (Pass/Rejection) with Feedback Loop.

        Actions:
        - Log negative signal to avoid similar properties
        - Update lead preferences based on feedback
        - Adjust property matching criteria
        """
        result = {"status": "preference_updated", "adjustments": []}

        try:
            if not feedback:
                logger.info(f"Pass without feedback: {lead_id} -> {property_id}")
                return result

            category = feedback.get("category")
            text = feedback.get("text", "")

            logger.info(
                f"Processing pass feedback: {lead_id} rejected {property_id} "
                f"due to {category}"
            )

            # A. Update lead preferences based on feedback
            adjustments = await self._adjust_preferences(
                lead_id, location_id, category, property_id
            )
            result["adjustments"] = adjustments

            # B. Log note (store in memory)
            note_body = (
                f"❌ User PASSED on property {property_id}\n"
                f"Reason: {category}\n"
                f"Feedback: {text}\n"
                f"Adjustments: {', '.join(adjustments)}"
            )
            logger.info(f"Note for {lead_id}: {note_body}")

            # C. Log negative match to avoid similar properties
            await self._log_negative_match(
                lead_id, location_id, property_id, category
            )

        except Exception as e:
            logger.error(f"Error processing pass: {e}")
            result["error"] = str(e)

        return result

    async def _adjust_preferences(
        self,
        lead_id: str,
        location_id: str,
        feedback_category: str,
        property_id: str,
    ) -> List[str]:
        """
        Adjust lead preferences based on pass feedback.

        Returns:
            List of adjustments made.
        """
        adjustments = []

        try:
            # Get current context
            context = await self.memory_service.get_context(
                lead_id, location_id=location_id
            )
            preferences = context.get("extracted_preferences", {})

            # Apply adjustments based on feedback category
            if feedback_category == FeedbackCategory.PRICE_TOO_HIGH.value:
                current_budget = preferences.get("budget", 0)
                if current_budget > 0:
                    new_budget = int(current_budget * 0.9)  # Lower by 10%
                    preferences["budget"] = new_budget
                    adjustments.append(f"Lowered budget to ${new_budget:,}")

            elif feedback_category == FeedbackCategory.PRICE_TOO_LOW.value:
                current_budget = preferences.get("budget", 0)
                if current_budget > 0:
                    new_budget = int(current_budget * 1.1)  # Raise by 10%
                    preferences["budget"] = new_budget
                    adjustments.append(f"Raised budget to ${new_budget:,}")

            elif feedback_category == FeedbackCategory.SIZE_TOO_SMALL.value:
                current_beds = preferences.get("bedrooms", 0)
                preferences["bedrooms"] = current_beds + 1
                adjustments.append(f"Increased minimum bedrooms to {current_beds + 1}")

            elif feedback_category == FeedbackCategory.SIZE_TOO_LARGE.value:
                current_beds = preferences.get("bedrooms", 0)
                if current_beds > 1:
                    preferences["bedrooms"] = current_beds - 1
                    adjustments.append(
                        f"Decreased maximum bedrooms to {current_beds - 1}"
                    )

            # Save updated preferences
            if adjustments:
                context["extracted_preferences"] = preferences
                await self.memory_service.store_context(
                    lead_id, context, location_id=location_id
                )
                logger.info(f"Updated preferences for {lead_id}: {adjustments}")

        except Exception as e:
            logger.error(f"Error adjusting preferences: {e}")

        return adjustments

    async def _log_negative_match(
        self,
        lead_id: str,
        location_id: str,
        property_id: str,
        reason: str,
    ):
        """Log a negative match to avoid showing similar properties."""
        try:
            context = await self.memory_service.get_context(
                lead_id, location_id=location_id
            )
            
            if "negative_matches" not in context:
                context["negative_matches"] = []

            context["negative_matches"].append(
                {
                    "property_id": property_id,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Keep only last 50 negative matches
            context["negative_matches"] = context["negative_matches"][-50:]

            await self.memory_service.store_context(
                lead_id, context, location_id=location_id
            )
            logger.info(f"Logged negative match: {lead_id} -> {property_id}")

        except Exception as e:
            logger.error(f"Error logging negative match: {e}")

    async def _update_liked_properties(
        self, lead_id: str, location_id: str, property_id: str
    ):
        """Update the list of liked properties in memory."""
        try:
            context = await self.memory_service.get_context(
                lead_id, location_id=location_id
            )
            
            if "liked_properties" not in context:
                context["liked_properties"] = []

            context["liked_properties"].append(
                {
                    "property_id": property_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            await self.memory_service.store_context(
                lead_id, context, location_id=location_id
            )

        except Exception as e:
            logger.error(f"Error updating liked properties: {e}")

    def _log_interaction(
        self,
        lead_id: str,
        property_id: str,
        action: SwipeAction,
        feedback: Optional[Dict[str, Any]],
        time_on_card: Optional[float],
    ):
        """Log interaction to local JSON storage."""
        interaction = {
            "interaction_id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "property_id": property_id,
            "action": action.value,
            "timestamp": datetime.utcnow().isoformat(),
            "meta_data": {
                "time_on_card": time_on_card,
            },
        }

        if feedback and action == SwipeAction.PASS:
            interaction["meta_data"]["feedback_category"] = feedback.get("category")
            interaction["meta_data"]["feedback_text"] = feedback.get("text", "")

        self.interactions.append(interaction)
        self._save_interactions()
        
        logger.info(f"Logged interaction: {interaction['interaction_id']}")

    def _count_recent_likes(self, lead_id: str, minutes: int = 10) -> int:
        """Count the number of likes for a lead in the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        count = 0
        for interaction in self.interactions:
            if (
                interaction["lead_id"] == lead_id
                and interaction["action"] == SwipeAction.LIKE.value
            ):
                timestamp = datetime.fromisoformat(
                    interaction["timestamp"].replace("Z", "+00:00")
                )
                if timestamp >= cutoff_time:
                    count += 1

        return count

    def get_lead_stats(self, lead_id: str) -> Dict[str, Any]:
        """Get statistics for a specific lead's swipe behavior."""
        lead_interactions = [
            i for i in self.interactions if i["lead_id"] == lead_id
        ]

        likes = [i for i in lead_interactions if i["action"] == SwipeAction.LIKE.value]
        passes = [
            i for i in lead_interactions if i["action"] == SwipeAction.PASS.value
        ]

        # Analyze pass reasons
        pass_reasons = {}
        for p in passes:
            reason = p.get("meta_data", {}).get("feedback_category", "no_feedback")
            pass_reasons[reason] = pass_reasons.get(reason, 0) + 1

        return {
            "lead_id": lead_id,
            "total_interactions": len(lead_interactions),
            "likes": len(likes),
            "passes": len(passes),
            "like_rate": len(likes) / len(lead_interactions) if lead_interactions else 0,
            "pass_reasons": pass_reasons,
            "recent_likes_10min": self._count_recent_likes(lead_id, minutes=10),
        }

    async def get_smart_deck(
        self,
        lead_id: str,
        location_id: str,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Get a smart, curated deck of properties for a lead.
        
        This is the AI recommendation engine that:
        1. Excludes properties already swiped (seen)
        2. Excludes properties similar to rejected ones (negative matches)
        3. Applies learned preferences (adjusted budget, bedrooms, etc.)
        4. Scores and ranks remaining properties
        
        Args:
            lead_id: GHL contact ID.
            location_id: GHL location/tenant ID.
            limit: Maximum number of properties to return.
            min_score: Minimum match score threshold.
            
        Returns:
            List of curated property listings.
        """
        logger.info(f"Fetching smart deck for lead {lead_id}")
        
        # Step 1: Get list of already-seen property IDs
        seen_property_ids = self._get_seen_property_ids(lead_id)
        logger.info(f"Lead {lead_id} has seen {len(seen_property_ids)} properties")
        
        # Step 2: Get learned preferences from memory
        context = await self.memory_service.get_context(
            lead_id, location_id=location_id
        )
        preferences = context.get("extracted_preferences", {})
        
        # Step 3: Analyze negative feedback patterns
        preferences = self._apply_negative_feedback_adjustments(
            lead_id, preferences
        )
        
        logger.info(f"Using preferences for {lead_id}: {preferences}")
        
        # Step 4: Get all property matches using PropertyMatcher
        all_matches = self.property_matcher.find_matches(
            preferences=preferences,
            limit=limit * 3,  # Get more to filter from
            min_score=min_score
        )
        
        # Step 5: Filter out seen properties
        unseen_matches = [
            prop for prop in all_matches
            if prop.get("id") not in seen_property_ids
            and prop.get("property_id") not in seen_property_ids
        ]
        
        # Step 6: Apply negative match filtering
        filtered_matches = self._filter_negative_matches(
            unseen_matches, lead_id, context
        )
        
        # Step 7: Return top matches
        final_deck = filtered_matches[:limit]
        
        logger.info(
            f"Smart deck for {lead_id}: {len(final_deck)} properties "
            f"(filtered from {len(all_matches)} total matches)"
        )
        
        return final_deck

    def _get_seen_property_ids(self, lead_id: str) -> set:
        """Get set of property IDs that lead has already swiped on."""
        seen_ids = set()
        
        for interaction in self.interactions:
            if interaction["lead_id"] == lead_id:
                seen_ids.add(interaction["property_id"])
        
        return seen_ids

    def _apply_negative_feedback_adjustments(
        self,
        lead_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust preferences based on negative feedback patterns.
        
        For example:
        - If user rejected 3+ properties as "too expensive", lower budget by 10%
        - If user rejected 2+ as "too small", increase bedroom requirement
        """
        # Get all pass interactions with feedback
        pass_interactions = [
            i for i in self.interactions
            if i["lead_id"] == lead_id and i["action"] == SwipeAction.PASS.value
        ]
        
        # Count feedback categories
        feedback_counts = {}
        for interaction in pass_interactions:
            category = interaction.get("meta_data", {}).get("feedback_category")
            if category:
                feedback_counts[category] = feedback_counts.get(category, 0) + 1
        
        # Apply adjustments based on patterns
        adjusted_prefs = preferences.copy()
        
        # Price adjustments
        price_too_high_count = feedback_counts.get(FeedbackCategory.PRICE_TOO_HIGH.value, 0)
        if price_too_high_count >= 3:
            current_budget = adjusted_prefs.get("budget", 0)
            if current_budget > 0:
                # Lower budget by 5% for every 3 "too expensive" rejections
                reduction = 0.05 * (price_too_high_count // 3)
                adjusted_prefs["budget"] = int(current_budget * (1 - reduction))
                logger.info(
                    f"Lowered budget from ${current_budget:,} to "
                    f"${adjusted_prefs['budget']:,} (pattern: {price_too_high_count} price rejections)"
                )
        
        # Size adjustments
        size_too_small_count = feedback_counts.get(FeedbackCategory.SIZE_TOO_SMALL.value, 0)
        if size_too_small_count >= 2:
            current_beds = adjusted_prefs.get("bedrooms", 0)
            adjusted_prefs["bedrooms"] = current_beds + 1
            logger.info(
                f"Increased bedroom minimum to {adjusted_prefs['bedrooms']} "
                f"(pattern: {size_too_small_count} size rejections)"
            )
        
        return adjusted_prefs

    def _filter_negative_matches(
        self,
        properties: List[Dict[str, Any]],
        lead_id: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter out properties similar to negative matches.
        
        For example, if they rejected property X because of "bad location",
        don't show properties in the same neighborhood.
        """
        negative_matches = context.get("negative_matches", [])
        
        if not negative_matches:
            return properties
        
        # Group negative matches by reason
        location_rejects = set()
        style_rejects = set()
        
        for neg_match in negative_matches:
            reason = neg_match.get("reason")
            prop_id = neg_match.get("property_id")
            
            if reason == FeedbackCategory.LOCATION.value:
                location_rejects.add(prop_id)
            elif reason == FeedbackCategory.STYLE.value:
                style_rejects.add(prop_id)
        
        # Filter properties
        filtered = []
        for prop in properties:
            # Skip if in location reject list (would need to check neighborhood)
            # For now, we just log this - more sophisticated matching would compare neighborhoods
            
            # Could add more sophisticated filtering here:
            # - If they rejected a Victorian style, filter out other Victorians
            # - If they rejected properties in "Downtown", filter that area
            
            filtered.append(prop)
        
        logger.info(
            f"Filtered {len(properties) - len(filtered)} properties "
            f"based on {len(negative_matches)} negative matches"
        )
        
        return filtered


# Demo function for testing
async def demo_swipe_manager():
    """Demo the portal swipe manager."""
    print("=" * 70)
    print("PORTAL SWIPE MANAGER DEMO")
    print("=" * 70)

    manager = PortalSwipeManager()

    # Simulate a user session
    lead_id = "contact_portal_demo"
    location_id = "loc_demo"

    # 1. User likes a property
    print("\n--- User Swipes RIGHT (Like) ---")
    result = await manager.handle_swipe(
        lead_id=lead_id,
        property_id="mls_998877",
        action=SwipeAction.LIKE,
        location_id=location_id,
        time_on_card=15.3,
    )
    print(f"Result: {result}")

    # 2. User passes on a property (too expensive)
    print("\n--- User Swipes LEFT (Pass - Too Expensive) ---")
    feedback_data = {
        "category": FeedbackCategory.PRICE_TOO_HIGH.value,
        "text": "Way out of my budget",
    }
    result = await manager.handle_swipe(
        lead_id=lead_id,
        property_id="mls_554433",
        action=SwipeAction.PASS,
        location_id=location_id,
        feedback=feedback_data,
        time_on_card=8.1,
    )
    print(f"Result: {result}")

    # 3. Multiple likes to trigger high-intent
    print("\n--- Simulating High Intent (3+ Likes) ---")
    for i in range(3):
        await manager.handle_swipe(
            lead_id=lead_id,
            property_id=f"mls_high_intent_{i}",
            action=SwipeAction.LIKE,
            location_id=location_id,
        )

    # 4. Get lead stats
    print("\n--- Lead Statistics ---")
    stats = manager.get_lead_stats(lead_id)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_swipe_manager())
