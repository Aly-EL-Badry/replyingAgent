from __future__ import annotations

import uuid

from pgvector.sqlalchemy  import Vector
from sqlalchemy           import Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm       import Mapped, mapped_column

from app.db.base import Base
from app.core.settings_constant import constants


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text:        Mapped[str]   = mapped_column(Text,    nullable=False)
    source:      Mapped[str]   = mapped_column(Text,    nullable=False, index=True)
    chunk_index: Mapped[int]   = mapped_column(Integer, nullable=False)
    embedding:   Mapped[list]  = mapped_column(
        Vector(constants.rag.embedding_dimension), nullable=True
    )
    created_at: Mapped[str] = mapped_column(
        Text, server_default=func.now().cast(Text)
    )

    __table_args__ = (
        
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk source={self.source!r} chunk={self.chunk_index}>"
