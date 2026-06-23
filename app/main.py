from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.db.mongodb.session import db_mongo

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi chạy kết nối MongoDB khi Server bắt đầu Start up
    try:
        db_mongo.connect_to_database()
        print("🚀 Đã kết nối tới MongoDB thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        
    yield
    
    # Khởi chạy khi Server đóng (Shutdown)
    db_mongo.close_database_connection()
    print("🛑 Đã đóng kết nối MongoDB.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Đăng ký các router chính thức của phiên bản v1 (Prefix: /api/v1)
from app.api.v1.router import api_router
app.include_router(api_router, prefix="/api/v1")

# Đăng ký trực tiếp router users lên root để hỗ trợ chuẩn endpoint GET /users/system-status
from app.api.v1.endpoints.users import router as users_router
app.include_router(users_router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return {
        "message": f"Chào mừng tới {settings.PROJECT_NAME}",
        "status": "Server đang chạy mượt mà!"
    }
