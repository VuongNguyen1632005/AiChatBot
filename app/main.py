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

# --- Đăng ký Exception Handlers toàn cục ---
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Bắt lỗi Validation từ Pydantic và định dạng lại theo cấu trúc chuẩn.
    """
    errors_list = []
    for error in exc.errors():
        field = error.get("loc")[-1] if error.get("loc") else None
        message = error.get("msg", "Dữ liệu không hợp lệ")
        
        # Làm sạch thông báo lỗi của Pydantic custom validators
        if message.startswith("Value error, "):
            message = message[len("Value error, "):]
            
        errors_list.append({
            "field": str(field) if field else None,
            "message": message
        })
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Dữ liệu không hợp lệ",
            "data": None,
            "errors": errors_list,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Bắt lỗi HTTPException của FastAPI và trả về chuẩn JSON của ETECHS.
    """
    errors_list = None
    if isinstance(exc.detail, list):
        errors_list = exc.detail
        message = "Dữ liệu không hợp lệ"
    elif isinstance(exc.detail, dict):
        errors_list = [exc.detail]
        message = exc.detail.get("message", "Đã xảy ra lỗi")
    else:
        message = str(exc.detail)
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "errors": errors_list,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Bắt các lỗi hệ thống không kiểm soát (500) và trả về thông báo an toàn.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Lỗi hệ thống nội bộ",
            "data": None,
            "errors": [{"field": None, "message": str(exc)}],
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
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
