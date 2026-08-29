from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import get_db_settings
import sys

db_settings = get_db_settings()
DATABASE_URL = str(db_settings.database_url)

is_celery = any("celery" in arg for arg in sys.argv)

if is_celery:
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
else:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class PostgresAdapter:
    """
    Adapter to manage PostgreSQL database sessions asynchronously.
    """

    @staticmethod
    async def get_db():
        """
        Dependency for FastAPI to provide an asynchronous database session per request.
        """
        async with AsyncSessionLocal() as db:
            yield db
