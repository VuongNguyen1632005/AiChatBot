from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Khởi tạo Async Engine cho PostgreSQL sử dụng asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Đặt thành True nếu muốn xem log các truy vấn SQL
    future=True
)

# Khởi tạo Sessionmaker để tạo các phiên làm việc (session) bất đồng bộ
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Dependency tiện ích để lấy database session cho các API endpoint sau này
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()