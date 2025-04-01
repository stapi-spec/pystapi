import re
from enum import Enum


class ConformanceClasses(Enum):
    """Enumeration class for Conformance Classes"""

    # defined conformance classes regexes
    CORE = "/core"
    OPPORTUNITIES = "/opportunities"
    ASYNC_OPPORTUNITIES = "/async-opportunities"

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
        return f"https://stapi.example.com/v0.1.*{self.value}"

    @property
    def pattern(self) -> re.Pattern[str]:
        return re.compile(rf"{re.escape('https://stapi.example.com/v0.1.')}(.*){re.escape(self.value)}")
