"""
Freemium — first N units are free, overage delegated to another strategy.

This is a great example of COMPOSITION: Freemium HAS-A inner PricingStrategy
rather than IS-A specific kind of pricing.

Example: 1000 free API calls per month, then ₹0.50 per call (UsageBased).
"""

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


class Freemium(PricingStrategy):

    def __init__(self, free_quota: int, overage_strategy: PricingStrategy):
        # Validate free_quota >= 0
        if free_quota < 0:
            raise ValueError("free_quota must be non-negative")
        
        # Validate overage_strategy is a PricingStrategy
        if not isinstance(overage_strategy, PricingStrategy):
            raise TypeError("overage_strategy must be a PricingStrategy")
        # Store both
        self.free_quota = free_quota
        self.overage_strategy = overage_strategy

    def calculate(self, quantity: int) -> Money:
        # Get currency from inner strategy
        currency = self.overage_strategy.calculate(0).currency

        # Within free quota -> free
        if quantity <= self.free_quota:
            return Money.zero(currency)

        # Over quota -> charge only the overage
        return self.overage_strategy.calculate(quantity - self.free_quota)
