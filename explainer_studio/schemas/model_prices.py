"""model-prices.toml in the user's config folder: the model prices dev mode works out dollars with.

Kept outside the package so prices change without a release. USD per million tokens. An entry applies from its
`effective_date` until the next entry for the same model and speed; usage before a model's first entry uses that entry.

    [[model_price]]
    model_name = "claude-opus-5-5"
    speed = "standard"
    effective_date = 2026-10-07
    non_cached_input_usd_per_million_tokens = 4
    cache_read_usd_per_million_tokens = 0.2
    five_minute_cache_write_usd_per_million_tokens = 5
    one_hour_cache_write_usd_per_million_tokens = 8
    output_usd_per_million_tokens = 20
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ModelPrice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_name: str
    speed: str = "standard"
    effective_date: date
    non_cached_input_usd_per_million_tokens: float = Field(ge=0)
    cache_read_usd_per_million_tokens: float = Field(ge=0)
    five_minute_cache_write_usd_per_million_tokens: float = Field(ge=0)
    one_hour_cache_write_usd_per_million_tokens: float = Field(ge=0)
    output_usd_per_million_tokens: float = Field(ge=0)


class ModelPrices(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    # TOML names each entry `[[model_price]]`
    model_prices: list[ModelPrice] = Field(default=[], alias="model_price")
