import re
from enum import Enum


class ConformanceClasses(Enum):
    """Enumeration class for Conformance Classes"""

    # defined conformance classes regexes
    # API-level classes (advertised in the root landing page / `/conformance`)
    CORE = "/core"
    ORDER_STATUSES = "/order-statuses"
    SEARCHES_OPPORTUNITY = "/searches-opportunity"
    SEARCHES_OPPORTUNITY_STATUSES = "/searches-opportunity-statuses"
    # Product-level classes (advertised in a Product's own `conformsTo`)
    OPPORTUNITIES = "/opportunities"
    ASYNC_OPPORTUNITIES = "/opportunities-async"

    @classmethod
    def get_by_name(cls, name: str) -> "ConformanceClasses":
        for member in cls:
            if member.name == name.upper():
                return member
        raise ValueError(f"Invalid conformance class '{name}'. Options are: {list(cls)}")

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return str(self)

    @property
    def valid_uri(self) -> str:
        return f"https://stapi.example.com/v*{self.value}"

    @property
    def pattern(self) -> re.Pattern[str]:
        return re.compile(rf"{re.escape('https://stapi.example.com/v')}[^/]+{re.escape(self.value)}\Z")
