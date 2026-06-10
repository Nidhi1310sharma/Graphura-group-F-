# ============================================================
# database.py - PostgreSQL Database Connection
# Uses SQLAlchemy async engine with asyncpg driver
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

# ---------------------------------------------------------------
# Convert postgresql:// URL to postgresql+asyncpg:// for async
# SQLAlchemy needs the asyncpg driver prefix for async operations
# ---------------------------------------------------------------
DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace(
    "postgres://", "postgresql+asyncpg://"
)

# Create the async engine
# echo=True logs all SQL statements (useful for debugging, turn off in production)
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,           # max number of connections in pool
    max_overflow=20,        # extra connections above pool_size
    pool_timeout=30,        # seconds to wait for connection
    pool_recycle=1800,      # recycle connections every 30 minutes
)

# Session factory - creates new async sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False   # keep objects usable after commit
)


# Base class for all ORM models
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------
# Dependency: FastAPI will call this to inject DB sessions
# into route handler functions automatically
# ---------------------------------------------------------------
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a database session.
    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Create all tables on startup (if they don't exist).
    For production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
