"""Dollars for model calls, worked out only for display in dev mode from the local price table.

The cost report records usage (`schemas/cost.py`); this turns model calls into an estimate, each call at the prices in
effect on its day. A model without a price in the table is left out and named.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date

from pydantic import ValidationError

from .dev_mode import check_is_dev_mode_on
from .errors import StudioError
from .schemas.cost import CostReportModelCall
from .schemas.model_prices import ModelPrice, ModelPrices
from .user_dirs import get_model_prices_file_path


def load_model_prices() -> list[ModelPrice] | None:
    """The price table, or None when there is none."""
    path = get_model_prices_file_path()
    if not path.exists():
        return None
    try:
        return ModelPrices.model_validate(tomllib.loads(path.read_text(encoding="utf-8"))).model_prices
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as error:
        raise StudioError(f"could not read the model price table {path}", str(error).splitlines()[0],
                          "fix the file (its format is in explainer_studio/schemas/model_prices.py) or remove it") \
            from None


def load_dev_mode_model_prices() -> tuple[list[ModelPrice] | None, str | None]:
    """The prices to show dollars with, and why there are none when the table cannot be read.

    No prices without dev mode or without a table: costs are then shown as usage only. A table that cannot be read
    never fails the command that shows the cost."""
    if not check_is_dev_mode_on():
        return None, None
    try:
        return load_model_prices(), None
    except StudioError as error:
        return None, f"{error.what}: {error.why}"


def _find_price_in_effect(prices: list[ModelPrice], model_call: CostReportModelCall, day: date) -> ModelPrice | None:
    matching_prices = sorted((price for price in prices
                      if price.model_name == model_call.model_name and price.speed == (model_call.speed or "standard")),
                     key=lambda price: price.effective_date)
    if not matching_prices:
        return None
    prices_in_effect = [price for price in matching_prices if price.effective_date <= day]
    return prices_in_effect[-1] if prices_in_effect else matching_prices[0]


@dataclass(frozen=True)
class CostEstimate:
    cost_usd: float  # the priced model calls
    unpriced_model_names: tuple[str, ...]  # names of the models the table has no price for, left out of `cost_usd`


def estimate_cost_usd(model_calls: list[CostReportModelCall], prices: list[ModelPrice]) -> CostEstimate:
    """Each call at the prices in effect on its day."""
    cost_usd, unpriced_model_names = 0.0, []
    for model_call in model_calls:
        price = _find_price_in_effect(prices, model_call, model_call.called_at.date())
        if price is None:
            unpriced_model_names.append(model_call.model_name)
            continue
        token_usage = model_call.token_usage
        cost_usd += (token_usage.non_cached_input_tokens * price.non_cached_input_usd_per_million_tokens
                + token_usage.cache_read_tokens * price.cache_read_usd_per_million_tokens
                + token_usage.five_minute_cache_write_tokens * price.five_minute_cache_write_usd_per_million_tokens
                + token_usage.one_hour_cache_write_tokens * price.one_hour_cache_write_usd_per_million_tokens
                + token_usage.output_tokens * price.output_usd_per_million_tokens) / 1e6
    return CostEstimate(cost_usd, tuple(dict.fromkeys(unpriced_model_names)))
