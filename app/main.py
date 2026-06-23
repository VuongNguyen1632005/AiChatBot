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

tags_metadata = [
    {
        "name": "Người dùng & Xác thực",
        "description": "Quản lý đăng ký, đăng nhập, hồ sơ và kiểm tra trạng thái hệ thống.",
    },
    {
        "name": "Quản lý Học liệu (RAG)",
        "description": "Tải lên tài liệu học tập (PDF, DOCX, TXT) phục vụ RAG và sinh đề thi.",
    },
    {
        "name": "Ma trận đề thi",
        "description": "Thiết lập cấu trúc đề thi, số lượng câu hỏi và phân bổ độ khó.",
    },
    {
        "name": "Sinh đề thi (AI)",
        "description": "Tự động sinh đề thi và xuất bản file Word/PDF sử dụng AI.",
    },
]

app = FastAPI(
    title="AI Chatbot & Exam Generator API",
    description="""
    Hệ thống API backend cho ứng dụng **AI Chatbot sinh đề thi thông minh**.
    
    ### Tính năng chính:
    * **Xác thực người dùng**: Đăng ký, đăng nhập và lấy Access Token JWT.
    * **Quản lý học liệu**: Tải lên và lưu trữ tài liệu học tập phục vụ RAG.
    * **Quản lý ma trận đề thi**: Thiết lập cấu trúc phân bổ câu hỏi.
    * **Sinh đề thi AI**: Tự động sinh câu hỏi chất lượng cao từ học liệu bằng AI.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

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
