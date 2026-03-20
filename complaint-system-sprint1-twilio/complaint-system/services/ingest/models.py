import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    user_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:        Mapped[str | None] = mapped_column(String(200))
    email_masked:Mapped[str | None] = mapped_column(String(200))
    phone_masked:Mapped[str | None] = mapped_column(String(20))
    tier:        Mapped[str]        = mapped_column(String(10), default="standard")
    created_at:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    user_id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    channel:          Mapped[str]       = mapped_column(String(20), nullable=False)
    message_original: Mapped[str]       = mapped_column(Text, nullable=False)
    status:           Mapped[str]       = mapped_column(String(30), default="received")
    schema_version:   Mapped[str]       = mapped_column(String(10), default="v1.0")
    created_at:       Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:       Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type:   Mapped[str]       = mapped_column(String(50), nullable=False)
    old_value:    Mapped[dict | None] = mapped_column(JSONB)
    new_value:    Mapped[dict | None] = mapped_column(JSONB)
    actor_type:   Mapped[str]       = mapped_column(String(10), default="system")
    created_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
