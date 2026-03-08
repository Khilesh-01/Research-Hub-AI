from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://Smartbridge:Smartbridge123@localhost:5432/ResearchHub",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_schema_migrations() -> None:
    """Apply incremental schema changes that SQLAlchemy won't handle automatically."""
    try:
        with engine.connect() as conn:
            # Add title column to chat_sessions if not present
            conn.execute(text(
                "ALTER TABLE chat_sessions "
                "ADD COLUMN IF NOT EXISTS title VARCHAR(255) DEFAULT 'New Chat'"
            ))
            conn.commit()
        logger.info("Schema migrations applied.")
    except Exception as e:
        logger.warning(f"Schema migration warning (non-fatal): {e}")


def init_db() -> None:
    """Kept for backward compatibility — schema migrations now done in run_schema_migrations."""
    pass


def create_tables(base) -> None:
    """Create all tables individually, skipping any that fail (e.g. paper_chunks needs pgvector)."""
    for table in base.metadata.sorted_tables:
        try:
            table.create(bind=engine, checkfirst=True)
            logger.info(f"Table '{table.name}' ready.")
        except Exception as e:
            logger.warning(f"Skipping table '{table.name}': {e}")
