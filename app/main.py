from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text  # Thêm dòng này để tạo câu lệnh test SQL
from app.core.config import settings
from app.db.mongodb.session import db_mongo
from app.db.postgresql.session import engine  # Import engine của Postgres vào đây

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- THỬ KẾT NỐI POSTGRESQL ----
    try:
        async with engine.connect() as connection:
            # Chạy thử một câu lệnh SQL đơn giản để test kết nối
            await connection.execute(text("SELECT 1"))
        print("🚀 Kết nối thành công tới PostgreSQL qua Docker!")
    except Exception as e:
        print(f"❌ Lỗi kết nối PostgreSQL: {e}")

    # ---- THỬ KẾT NỐI MONGODB ----
    try:
        db_mongo.connect_to_database()
        print("🚀 Kết nối thành công tới MongoDB qua Docker!")
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        
    yield
    
    # Khởi chạy khi Server đóng (Shutdown)
    db_mongo.close_database_connection()
    print("🛑 Đã đóng kết nối MongoDB.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "message": f"Chào mừng tới {settings.PROJECT_NAME}",
        "status": "Server đang chạy mượt mà!"
    }