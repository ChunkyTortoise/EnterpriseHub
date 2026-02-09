from typing import Any, Dict

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowFactory:
    """
    Factory class to instantiate and manage Lead (Buyer) and Seller workflows.
    """

    _instances: Dict[str, Any] = {}

    @classmethod
    def get_workflow(cls, workflow_type: str, conversation_manager=None, ghl_client=None) -> Any:
        """
        Get or create a workflow instance based on type.

        Args:
            workflow_type: "buyer" or "seller"
            conversation_manager: Optional conversation manager instance
            ghl_client: Optional GHL client instance

        Returns:
            Workflow instance (LeadBotWorkflow or JorgeSellerWorkflow)
        """
        if workflow_type == "buyer":
            if "buyer" not in cls._instances:
                logger.info("Initializing LeadBotWorkflow (Buyer)")
                cls._instances["buyer"] = LeadBotWorkflow(ghl_client)
            return cls._instances["buyer"]

        elif workflow_type == "seller":
            if "seller" not in cls._instances:
                logger.info("Initializing JorgeSellerBot (Seller)")
                cls._instances["seller"] = JorgeSellerBot(conversation_manager, ghl_client)
            return cls._instances["seller"]

        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")


def get_workflow_factory() -> WorkflowFactory:
    return WorkflowFactory()
