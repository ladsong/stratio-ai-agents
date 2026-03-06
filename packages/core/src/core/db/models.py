from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from core.db.base import Base, TimestampMixin


class Thread(Base, TimestampMixin):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    events: Mapped[list["Event"]] = relationship("Event", back_populates="thread")
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="thread")


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    thread_id: Mapped[str] = mapped_column(ForeignKey("threads.id"), nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    thread: Mapped["Thread"] = relationship("Thread", back_populates="events")


class Run(Base, TimestampMixin):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    thread_id: Mapped[str] = mapped_column(ForeignKey("threads.id"), nullable=False)
    graph_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    thread: Mapped["Thread"] = relationship("Thread", back_populates="runs")
    approvals: Mapped[list["RunApproval"]] = relationship("RunApproval", back_populates="run")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="run")
    tool_calls: Mapped[list["ToolCall"]] = relationship("ToolCall", back_populates="run")


class RunApproval(Base, TimestampMixin):
    __tablename__ = "run_approvals"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="approvals")


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="artifacts")


class ToolCall(Base, TimestampMixin):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="tool_calls")


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="document")


class KnowledgeChunk(Base, TimestampMixin):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536), nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship("KnowledgeDocument", back_populates="chunks")


class GraphRegistry(Base, TimestampMixin):
    __tablename__ = "graph_registry"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ToolRegistry(Base, TimestampMixin):
    __tablename__ = "tool_registry"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timeout_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    permission_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class IntegrationCredential(Base, TimestampMixin):
    __tablename__ = "integration_credentials"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    integration_type: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="valid")
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ToolPolicy(Base, TimestampMixin):
    __tablename__ = "tool_policies"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="allowlist")
    tools: Mapped[dict] = mapped_column(JSON, nullable=False)
