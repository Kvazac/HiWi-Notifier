from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Listing:
    listing_id: str
    title: str
    link: str
    description: str
    published: Optional[datetime]
    author: str = ""

    @property
    def searchable_text(self) -> str:
        return f"{self.title}\n{self.description}\n{self.author}".strip()
