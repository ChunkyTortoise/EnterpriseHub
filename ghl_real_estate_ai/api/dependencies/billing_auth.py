"""
Billing Location Authorization Dependency

Enforces location-level IDOR protection: ensures users can only access
subscriptions belonging to their own GHL location.
"""

from fastapi import Depends, HTTPException, status

from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


async def get_billing_location(current_user=Depends(get_current_user)) -> str:
    """
    Extract and validate the location_id from the current authenticated user.

    Returns:
        location_id associated with the authenticated user

    Raises:
        HTTPException 403: If user has no location_id
    """
    location_id = getattr(current_user, "location_id", None)
    if not location_id:
        logger.warning(
            "Billing access denied: user has no location_id",
            extra={"user_id": getattr(current_user, "id", "unknown")},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "no_location_associated",
                "error_message": "No location is associated with this user account",
                "error_type": "authorization",
                "recoverable": False,
            },
        )
    return location_id


async def verify_subscription_ownership(
    subscription_id: int,
    location_id: str = Depends(get_billing_location),
) -> int:
    """
    Verify the authenticated user owns the given subscription.

    Queries the subscriptions table to confirm location_id matches
    the user's location before allowing the operation.

    Returns:
        subscription_id if ownership is confirmed

    Raises:
        HTTPException 403: If user does not own the subscription
        HTTPException 404: If subscription does not exist
    """
    from ghl_real_estate_ai.services.database_service import get_database

    db = await get_database()
    async with db.get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, location_id FROM subscriptions WHERE id = $1",
            subscription_id,
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "subscription_not_found",
                "error_message": f"Subscription {subscription_id} not found",
                "error_type": "not_found",
                "recoverable": True,
            },
        )

    if row["location_id"] != location_id:
        logger.warning(
            "IDOR attempt: location mismatch on subscription access",
            extra={
                "user_location": location_id,
                "subscription_id": subscription_id,
                "subscription_location": row["location_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "subscription_access_denied",
                "error_message": "You do not have access to this subscription",
                "error_type": "authorization",
                "recoverable": False,
            },
        )

    return subscription_id
