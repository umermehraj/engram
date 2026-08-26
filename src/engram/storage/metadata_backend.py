"""SQLAlchemy metadata backend (SQLite local / PostgreSQL cloud)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, JSON, Integer, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from engram.config import EngramConfig
from engram.storage.base import MetadataBackend


# ── ORM Models ───────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


class TenantRow(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="")
    api_key_hash: Mapped[str] = mapped_column(String, default="")
    plan: Mapped[str] = mapped_column(String, default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    external_id: Mapped[str] = mapped_column(String, default="")
    metadata_json: Mapped[str] = mapped_column(String, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    agent_id: Mapped[str] = mapped_column(String, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IngestionLogRow(Base):
    __tablename__ = "ingestion_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    session_id: Mapped[str] = mapped_column(String, default="")
    entities_created: Mapped[int] = mapped_column(Integer, default=0)
    relationships_created: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Backend ──────────────────────────────────────────────────────────────────


class MetadataBackend(MetadataBackend):
    def __init__(self, config: EngramConfig) -> None:
        self.config = config
        self._engine = None
        self._session_factory = None

    async def initialize(self) -> None:
        # Ensure parent dir exists for SQLite
        if self.config.local:
            self.config.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_async_engine(
            self.config.effective_database_url,
            echo=False,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _get_session(self) -> AsyncSession:
        assert self._session_factory is not None
        return self._session_factory()

    async def ensure_tenant(self, tenant_id: str, name: str = "") -> None:
        async with self._get_session() as session:
            existing = await session.get(TenantRow, tenant_id)
            if not existing:
                session.add(TenantRow(id=tenant_id, name=name))
                await session.commit()

    async def ensure_user(self, user_id: str, tenant_id: str) -> None:
        async with self._get_session() as session:
            existing = await session.get(UserRow, user_id)
            if not existing:
                session.add(UserRow(id=user_id, tenant_id=tenant_id))
                await session.commit()

    async def log_ingestion(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        entities_created: int,
        relationships_created: int,
    ) -> None:
        async with self._get_session() as session:
            session.add(IngestionLogRow(
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                entities_created=entities_created,
                relationships_created=relationships_created,
            ))
            await session.commit()

    async def get_tenant_by_api_key_hash(self, api_key_hash: str) -> TenantRow | None:
        async with self._get_session() as session:
            result = await session.execute(
                select(TenantRow).where(TenantRow.api_key_hash == api_key_hash)
            )
            return result.scalar_one_or_none()

    async def delete_user_data(self, user_id: str, tenant_id: str) -> int:
        async with self._get_session() as session:
            # Count user rows
            count_result = await session.execute(
                select(func.count()).select_from(UserRow).where(
                    UserRow.id == user_id, UserRow.tenant_id == tenant_id
                )
            )
            count = count_result.scalar() or 0

            # Delete ingestion logs
            await session.execute(
                delete(IngestionLogRow).where(
                    IngestionLogRow.user_id == user_id,
                    IngestionLogRow.tenant_id == tenant_id,
                )
            )
            # Delete sessions
            await session.execute(
                delete(SessionRow).where(SessionRow.user_id == user_id)
            )
            # Delete user
            await session.execute(
                delete(UserRow).where(
                    UserRow.id == user_id, UserRow.tenant_id == tenant_id
                )
            )
            await session.commit()
            return int(count)

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
