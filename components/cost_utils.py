"""Utility functions for calculating API costs."""

# Cost per token in USD based on model
MODEL_COSTS = {
    # GPT-4o versions
    "gpt-4o-2024-08-06": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-11-20": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
    # GPT-4o-mini versions
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
    # O1 versions
    "o1-2024-12-17": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
    "o1-preview-2024-09-12": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
    
    # O3-mini versions
    "o3-mini-2025-01-31": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
    
    # O1-mini versions
    "o1-mini-2024-09-12": {"input": 1.10, "cached_input": 0.55, "output": 4.40}
}

def calculate_costs(model_name, prompt_tokens, completion_tokens, is_cached=False):
    """
    Calculate costs based on token usage.
    
    Args:
        model_name (str): Name of the model being used
        prompt_tokens (int): Number of tokens in the prompt
        completion_tokens (int): Number of tokens in the completion
        is_cached (bool, optional): Whether to use cached input rate. Defaults to False.
    
    Returns:
        tuple: (input_cost, output_cost, total_cost) in USD
        Returns (None, None, None) if model is unknown
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if model_name not in MODEL_COSTS:
        logger.warning(f"Unknown model for cost calculation: {model_name}")
        return None, None, None
    
    costs = MODEL_COSTS[model_name]
    input_rate = costs["cached_input"] if is_cached and "cached_input" in costs else costs["input"]
    output_rate = costs["output"]
    
    input_cost = (prompt_tokens / 1000) * input_rate
    output_cost = (completion_tokens / 1000) * output_rate
    total_cost = input_cost + output_cost
    
    return input_cost, output_cost, total_cost 