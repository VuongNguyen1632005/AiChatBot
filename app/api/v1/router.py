from fastapi import APIRouter
from app.api.v1.endpoints import users, documents, exams, matrices

api_router = APIRouter()

# Đăng ký các router con vào api_router của v1
api_router.include_router(users.router, prefix="/users", tags=["Người dùng & Xác thực"])
api_router.include_router(documents.router, prefix="/documents", tags=["Quản lý Học liệu (RAG)"])
api_router.include_router(matrices.router, prefix="/matrices", tags=["Ma trận đề thi"])
api_router.include_router(exams.router, prefix="/exams", tags=["Sinh đề thi (AI)"])
