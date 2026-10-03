"""Payment gateway interface with dynamic dispatch."""

from typing import Any, Dict


def execute_payment_gateway(gateway_instance: Any, action_name: str, payload: Dict[str, Any]) -> Any:
    """Execute dynamic payment gateway method based on runtime action name.
    
    This dynamic dispatch creates an unresolved target for static analysis.
    """
    if hasattr(gateway_instance, action_name):
        handler = getattr(gateway_instance, action_name)
        return handler(payload)
    raise AttributeError(f"Gateway method {action_name} not found")
