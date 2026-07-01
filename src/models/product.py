"""
Product domain model.

Products are read-only from this service's point of view (Decision 3 -
Read-Only Product Catalog). They're preloaded at startup by
ProductRepository and never mutated through the API.
"""

from dataclasses import dataclass


@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float  # server-side source of truth for pricing (Assumption 9)
