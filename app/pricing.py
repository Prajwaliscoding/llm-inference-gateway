# The formula - standard across every LLM provider:
# cost = (prompt_tokens / 1,000,000) × input_price_per_million
#      + (completion_tokens / 1,000,000) × output_price_per_million


# source: https://openai.com/api/pricing/
# source: https://www.anthropic.com/pricing

# NOTE: prices change over time. Verify against source links before relying
# on cost figures for real billing decisions.


MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    # introductory rate through Aug 31, 2026. It becomes $3.00/$15.00 on Sep 1
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        return 0.0

    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost