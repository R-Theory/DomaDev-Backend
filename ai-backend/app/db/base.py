from __future__ import annotations

import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import get_settings

Base = declarative_base()
_engine = None
SessionLocal = None


def init_engine() -> None:
    global _engine, SessionLocal
    settings = get_settings()
    url = settings.database_url
    connect_args = {}
    if url.startswith("sqlite"):
        # Ensure directory exists for local file path
        if "///" in url:
            path = url.split("///", 1)[1]
        else:
            path = ""
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        # Increase default timeout to handle busy DB
        connect_args = {"check_same_thread": False, "timeout": 30.0}

    _engine = create_engine(url, echo=settings.db_echo, pool_pre_ping=True, connect_args=connect_args)

    if url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _):
            # Make SQLite more robust on Windows/UNC paths
            cur = dbapi_conn.cursor()
            try:
                # Busy timeout for locked DB
                cur.execute("PRAGMA busy_timeout=5000;")
                # Try to enable WAL; if it fails (e.g., network/UNC), ignore
                try:
                    cur.execute("PRAGMA journal_mode=WAL;")
                except Exception:
                    pass
                cur.execute("PRAGMA synchronous=NORMAL;")
                cur.execute("PRAGMA foreign_keys=ON;")
            finally:
                cur.close()

    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_session():
    if SessionLocal is None:
        init_engine()
    return SessionLocal()


def create_all() -> None:
    if _engine is None:
        init_engine()
    # Import models to register metadata
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=_engine)

    # Create FTS5 tables/triggers for SQLite
    url = get_settings().database_url
    if url.startswith("sqlite"):
        with _engine.begin() as conn:  # type: ignore[arg-type]
            conn.exec_driver_sql(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    message_id UNINDEXED,
                    conversation_id UNINDEXED,
                    content_text,
                    role UNINDEXED
                );
                """
            )
            # Insert trigger
            conn.exec_driver_sql(
                """
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO messages_fts(message_id, conversation_id, content_text, role)
                    VALUES (new.id, new.conversation_id, coalesce(new.content_text, ''), new.role);
                END;
                """
            )
            # Update trigger (delete+insert)
            conn.exec_driver_sql(
                """
                CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE OF content_text, role, conversation_id ON messages BEGIN
                    DELETE FROM messages_fts WHERE message_id = old.id;
                    INSERT INTO messages_fts(message_id, conversation_id, content_text, role)
                    VALUES (new.id, new.conversation_id, coalesce(new.content_text, ''), new.role);
                END;
                """
            )
            # Delete trigger
            conn.exec_driver_sql(
                """
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                    DELETE FROM messages_fts WHERE message_id = old.id;
                END;
                """
            )


