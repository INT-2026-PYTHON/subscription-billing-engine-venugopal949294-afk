"""
TieredPricing — different price per unit depending on the tier the quantity falls into.

This is the "cumulative" / "stacked" tier model, NOT the "volume" model:
    Tiers: [(0, 1000, ₹2.00), (1000, 5000, ₹1.50), (5000, None, ₹1.00)]
    Quantity = 6000:
        First 1000 units  @ ₹2.00 = ₹2000
        Next  4000 units  @ ₹1.50 = ₹6000
        Last  1000 units  @ ₹1.00 = ₹1000
        ------------------------------------
        Total                     = ₹9000

A tier with `to_units = None` is the open-ended top tier.

Tier boundaries are HALF-OPEN on the right: a tier (from, to, price)
covers units strictly less than `to` (i.e. [from, to)).
"""

from dataclasses import dataclass
from typing import Optional

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


@dataclass(frozen=True)
class Tier:
    from_units: int
    to_units: int | None   # None means_open-ended
    unit_price: Money


class TieredPricing(PricingStrategy):

    def __init__(self, tiers: list[Tier]) -> None:
        # Reject empty tier list
        if not tiers:
            raise ValueError("tiers cannot be empty")

        #  Walk through tiers: contiguous check + only last has to_units=None
        for i in range(len(tiers) - 1):          # all except the last
            if tiers[i].to_units is None:
                raise ValueError(
                    f"Only the last tier can have to_units=None "
                    f"(violated at tier index {i})"
                )
            
            if tiers[i + 1].from_units != tiers[i].to_units:
                raise ValueError(
                    f"Tiers are not contiguous: "
                    f"tiers[{i}].to_units={tiers[i].to_units} "
                    f"!= tiers[{i+1}].from_units={tiers[i+1].from_units}"
                )

        # Check every unit_price shares the same currency
        currency = tiers[0].unit_price.currency
        for i, tier in enumerate(tiers):
            if tier.unit_price.currency != currency:
                raise ValueError(
                    f"Currency mismatch at tier {i}: "
                    f"expected {currency}, got {tier.unit_price.currency}"
                )

        self.tiers = tiers

    def calculate(self, quantity: int) -> Money:
        # Reject negative quantity
        if quantity < 0:
            raise ValueError("quantity must be non-negative")

        #  Use currency of first tier
        currency = self.tiers[0].unit_price.currency

        # Start total at zero
        total = Money.zero(currency)

        for tier in self.tiers:
            if tier.to_units is None:
                # Open-ended tier
                if quantity > tier.from_units:
                    units_in_tier = quantity - tier.from_units
                else:
                    units_in_tier = 0
            else:
            # Bounded tier
                if quantity > tier.from_units:
                    units_in_tier = min(quantity, tier.to_units) - tier.from_units
                else:
                    units_in_tier = 0

            total = total + tier.unit_price * units_in_tier

        return total