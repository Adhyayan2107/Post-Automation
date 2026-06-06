from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class RawContent:
    url: str
    title: str
    source: str
    run_id: UUID
    body: str = ""
    id: UUID = field(default_factory=uuid4)
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
