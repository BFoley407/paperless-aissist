"""SQLite database engine and session management.

Provides both sync and async SQLModel session factories backed by SQLite,
with tables created on startup. The async engine uses aiosqlite.
"""

import os
import pathlib
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.pool import StaticPool

data_dir = os.environ.get("DATA_DIR", "/app/data")
pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{data_dir}/paperless-aissist.db"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{data_dir}/paperless-aissist.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables():
    """Create all tables defined by SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing an AsyncSession.

    Yields:
        An AsyncSession instance that auto-commits on success or rolls back on error.
    """
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Sync context manager providing a Session.

    Yields:
        A Session instance that auto-commits on success or rolls back on error.
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def run_migrations(database_url: str = DATABASE_URL) -> None:
    """Run Alembic migrations, bringing the database to head.

    For a database that predates Alembic (tables present but no alembic_version
    table) we stamp it to the BASE revision rather than head, then upgrade — so
    the later column/index migrations actually run instead of being skipped. The
    migrations are idempotent, so this is safe whether the pre-Alembic schema is
    old (missing newer columns) or already current.
    """
    import logging
    from alembic.config import Config
    from alembic import command
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine, inspect

    logger = logging.getLogger(__name__)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    insp_engine = create_engine(database_url)
    try:
        existing_tables = inspect(insp_engine).get_table_names()
    finally:
        insp_engine.dispose()

    if "alembic_version" not in existing_tables and len(existing_tables) > 0:
        base_rev = ScriptDirectory.from_config(alembic_cfg).get_base()
        logger.info(
            "Pre-Alembic database detected — stamping to base %s, then upgrading", base_rev
        )
        command.stamp(alembic_cfg, base_rev)

    logger.info("Running Alembic migrations...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations complete")
