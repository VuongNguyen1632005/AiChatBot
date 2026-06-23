from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app.db.postgresql.session import engine
from app.db.mongodb.session import db_mongo

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")

# Schemas
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

# Endpoints người dùng
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserRegister):
    """
    Đăng ký tài khoản người dùng mới.
    """
    return UserResponse(
        id="usr_mock_111",
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        is_active=True,
        created_at=datetime.utcnow()
    )

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Đăng nhập lấy Access Token (Hỗ trợ xác thực trực tiếp trên Swagger UI qua nút Authorize).
    """
    if form_data.username == "admin" and form_data.password == "admin123":
        return Token(access_token="mock_token_jwt_secret_xyz_123", token_type="bearer")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tên đăng nhập hoặc mật khẩu không đúng. Thử tài khoản 'admin' và mật khẩu 'admin123'"
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(token: str = Depends(oauth2_scheme)):
    """
    Lấy thông tin cá nhân của người dùng hiện tại đang đăng nhập.
    (Yêu cầu gửi kèm Bearer Token xác thực).
    """
    return UserResponse(
        id="usr_mock_111",
        username="admin",
        email="admin@example.com",
        full_name="Administrator",
        is_active=True,
        created_at=datetime.utcnow()
    )

@router.get("/system-status", status_code=status.HTTP_200_OK)
async def get_system_status():
    """
    Kiểm tra trạng thái hệ thống: kết nối database PostgreSQL, MongoDB và hoạt động của server.
    """
    postgresql_status = "healthy"
    mongodb_status = "healthy"
    errors = []

    # Kiểm tra kết nối PostgreSQL
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as e:
        postgresql_status = "unhealthy"
        errors.append(f"PostgreSQL error: {str(e)}")

    # Kiểm tra kết nối MongoDB
    try:
        if db_mongo.client is not None:
            await db_mongo.client.admin.command('ping')
        else:
            raise Exception("MongoDB client is not initialized")
    except Exception as e:
        mongodb_status = "unhealthy"
        errors.append(f"MongoDB error: {str(e)}")

    # Trạng thái tổng quát của server
    server_status = "healthy" if postgresql_status == "healthy" and mongodb_status == "healthy" else "unhealthy"

    return {
        "status": server_status,
        "services": {
            "server": "healthy",
            "postgresql": postgresql_status,
            "mongodb": mongodb_status
        },
        "errors": errors if errors else None
    }
