from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Schemas
class MatrixQuestionDistribution(BaseModel):
    difficulty: str  # 'de', 'trung_binh', 'kho'
    quantity: int = Field(..., description="Số lượng câu hỏi")

class MatrixCreate(BaseModel):
    title: str = Field(..., example="Ma trận đề thi Học kỳ I Tin học 10")
    description: Optional[str] = Field(None, example="Cấu trúc đề thi Tin học 10 bao gồm trắc nghiệm và tự luận")
    total_questions: int = Field(..., example=40)
    distribution: List[MatrixQuestionDistribution]

class MatrixResponse(MatrixCreate):
    id: str
    created_at: datetime
    updated_at: datetime

# Sơ bộ các endpoint ma trận đề thi
@router.post("/", response_model=MatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_matrix(matrix: MatrixCreate):
    """
    Tạo mới một ma trận đề thi (Cấu trúc phân bổ câu hỏi theo độ khó/chủ đề).
    """
    return MatrixResponse(
        id="matrix_mock_789",
        title=matrix.title,
        description=matrix.description,
        total_questions=matrix.total_questions,
        distribution=matrix.distribution,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.get("/", response_model=List[MatrixResponse])
async def list_matrices():
    """
    Lấy danh sách các ma trận đề thi đã tạo.
    """
    return [
        MatrixResponse(
            id="matrix_mock_789",
            title="Ma trận đề thi Học kỳ I Tin học 10",
            description="Cấu trúc đề thi Tin học 10 bao gồm trắc nghiệm và tự luận",
            total_questions=40,
            distribution=[
                MatrixQuestionDistribution(difficulty="de", quantity=20),
                MatrixQuestionDistribution(difficulty="trung_binh", quantity=15),
                MatrixQuestionDistribution(difficulty="kho", quantity=5)
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]

@router.get("/{matrix_id}", response_model=MatrixResponse)
async def get_matrix(matrix_id: str):
    """
    Lấy thông tin chi tiết một ma trận đề thi.
    """
    return MatrixResponse(
        id=matrix_id,
        title="Ma trận đề thi Học kỳ I Tin học 10",
        description="Cấu trúc đề thi Tin học 10 bao gồm trắc nghiệm và tự luận",
        total_questions=40,
        distribution=[
            MatrixQuestionDistribution(difficulty="de", quantity=20),
            MatrixQuestionDistribution(difficulty="trung_binh", quantity=15),
            MatrixQuestionDistribution(difficulty="kho", quantity=5)
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.put("/{matrix_id}", response_model=MatrixResponse)
async def update_matrix(matrix_id: str, matrix: MatrixCreate):
    """
    Cập nhật thông tin cấu trúc ma trận đề thi.
    """
    return MatrixResponse(
        id=matrix_id,
        title=matrix.title,
        description=matrix.description,
        total_questions=matrix.total_questions,
        distribution=matrix.distribution,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.delete("/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matrix(matrix_id: str):
    """
    Xóa ma trận đề thi.
    """
    return None
