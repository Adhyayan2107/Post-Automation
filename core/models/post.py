from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, TEXT


class PostStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    body: str
    post_type: str
    creative_angle: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    image_subject: Optional[str] = Field(default=None)
    gcal_event_id: Optional[str] = Field(default=None)
    source_urls: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(TEXT), nullable=False, server_default="{}"))
    target_platforms: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(TEXT), nullable=False, server_default="{}"))
    target_subreddits: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(TEXT), nullable=False, server_default="{}"))
    status: PostStatus = Field(default=PostStatus.PENDING)
    scheduled_at: Optional[datetime] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_id: UUID
