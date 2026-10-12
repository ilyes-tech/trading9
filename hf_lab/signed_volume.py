"""Closed M1 signed taker-volume feature; no execution or admission logic.

Implements the existing multimarket_question_builder_v1 definition.
The timestamp denotes bar start. None means unavailable, never a neutral signal.
This is a trade-volume imbalance, not an order-book or causal measurement.
"""

import math


def closed_m1_imbalance(*, bar_start, as_of, buy_volume, sell_volume):
    """Return (buy-sell)/(buy+sell) only after the full minute closes.

    Invalid inputs raise ValueError. Unclosed and zero-volume bars return None.
    Caller must additionally enforce actual data arrival time before trading.
    """
    inputs = (bar_start, as_of, buy_volume, sell_volume)
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in inputs):
        raise ValueError("Expected finite numeric inputs")
    try:
        finite = all(math.isfinite(x) for x in inputs)
    except OverflowError as exc:
        raise ValueError("Input outside finite numeric range") from exc
    if not finite:
        raise ValueError("Expected finite numeric inputs")
    if bar_start < 0 or bar_start % 60 != 0 or as_of < 0:
        raise ValueError("Expected nonnegative timestamps and aligned M1 start")
    if buy_volume < 0 or sell_volume < 0:
        raise ValueError("Negative volume")
    if as_of < bar_start + 60:
        return None
    scale = max(buy_volume, sell_volume)
    if scale == 0:
        return None
    # Scaling avoids overflow for large but finite volumes.
    buy, sell = buy_volume / scale, sell_volume / scale
    return (buy - sell) / (buy + sell)
