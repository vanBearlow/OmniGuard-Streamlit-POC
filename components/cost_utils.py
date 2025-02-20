"""Utility functions for calculating API costs with clearly defined cost models.

This module uses token counts and cost-per-token rates based on the model name
to compute the input, output, and total costs in USD. If an unknown model is encountered,
the function returns None values.
"""

import logging
from typing import Dict, Tuple, Optional

logger: logging.Logger = logging.getLogger(__name__)

#*** COST MODELS CONFIGURATION ***
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "gpt-4o-2024-08-06":     {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-11-20":     {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-05-13":     {"input": 5.00,                        "output": 15.00},
    "gpt-4o-mini-2024-07-18":{"input": 0.15, "cached_input": 0.075, "output": 0.60},
    "o1-2024-12-17":         {"input": 15.00, "cached_input": 7.50,  "output": 60.00},
    "o1-preview-2024-09-12": {"input": 15.00, "cached_input": 7.50,  "output": 60.00},
    "o3-mini-2025-01-31":    {"input": 1.10,  "cached_input": 0.55,  "output": 4.40},
    "o1-mini-2024-09-12":    {"input": 1.10,  "cached_input": 0.55,  "output": 4.40},
}


def calculate_costs(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    is_cached: bool = False,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Calculate and return the cost for prompt and completion tokens based on the model's pricing.

    Args:
        model_name (str): Name of the model being used; this key is used in the cost configuration.
        prompt_tokens (int): The number of tokens in the prompt.
        completion_tokens (int): The number of tokens in the generated completion.
        is_cached (bool, optional): Flag indicating if the cached pricing should be applied. Defaults to False.

    Returns:
        Tuple[Optional[float], Optional[float], Optional[float]]:
            A tuple containing (input_cost, output_cost, total_cost) in USD, or
            (None, None, None) if the model is unknown.
    """
    if model_name not in MODEL_COSTS:
        logger.warning(f"Unknown model for cost calculation: {model_name}")
        return None, None, None

    costs: Dict[str, float] = MODEL_COSTS[model_name]
    # Use the cached input rate if available and if the flag is set; otherwise fall back to the regular input rate.
    input_rate: float = costs.get("cached_input", costs["input"]) if is_cached and "cached_input" in costs else costs["input"]
    output_rate: float = costs["output"]

    input_cost: float = (prompt_tokens / 1000) * input_rate
    output_cost: float = (completion_tokens / 1000) * output_rate
    total_cost: float = input_cost + output_cost

    return input_cost, output_cost, total_cost 