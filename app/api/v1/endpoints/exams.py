from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Schemas
class ExamQuestion(BaseModel):
    id: str
    question_text: str
    options: Optional[List[str]] = Field(None, description="Các phương án lựa chọn đối với trắc nghiệm")
    correct_answer: str
    difficulty: str
    score: float

class ExamGenerateRequest(BaseModel):
    matrix_id: str = Field(..., description="ID của ma trận đề thi áp dụng")
    document_id: Optional[str] = Field(None, description="ID học liệu để AI đọc và trích xuất câu hỏi (RAG)")
    prompt_customize: Optional[str] = Field(None, example="Tập trung vào phần mạng máy tính và bảo mật")

class ExamResponse(BaseModel):
    id: str
    title: str
    matrix_id: str
    document_id: Optional[str]
    questions: List[ExamQuestion]
    created_at: datetime

# Sơ bộ các endpoint sinh đề thi
@router.post("/generate", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def generate_exam(payload: ExamGenerateRequest):
    """
    Sinh đề thi tự động bằng trí tuệ nhân tạo (AI) dựa vào Ma trận đề thi và Học liệu (RAG).
    """
    # Trả về kết quả đề thi sinh mẫu
    return ExamResponse(
        id="exam_mock_999",
        title="Đề thi trắc nghiệm học kỳ I - Tin học 10",
        matrix_id=payload.matrix_id,
        document_id=payload.document_id,
        questions=[
            ExamQuestion(
                id="q1",
                question_text="RAM là viết tắt của cụm từ nào?",
                options=["Read Access Memory", "Random Access Memory", "Run Action Memory", "Ready Auto Memory"],
                correct_answer="Random Access Memory",
                difficulty="de",
                score=0.25
            ),
            ExamQuestion(
                id="q2",
                question_text="Hệ điều hành là gì?",
                options=[
                    "Phần cứng máy tính",
                    "Phần mềm ứng dụng",
                    "Phần mềm hệ thống quản lý phần cứng và phần mềm khác",
                    "Thiết bị ngoại vi"
                ],
                correct_answer="Phần mềm hệ thống quản lý phần cứng và phần mềm khác",
                difficulty="trung_binh",
                score=0.25
            )
        ],
        created_at=datetime.utcnow()
    )

@router.get("/", response_model=List[ExamResponse])
async def list_exams():
    """
    Lấy danh sách các đề thi đã được tạo/sinh tự động trước đó.
    """
    return [
        ExamResponse(
            id="exam_mock_999",
            title="Đề thi trắc nghiệm học kỳ I - Tin học 10",
            matrix_id="matrix_mock_789",
            document_id="doc_mock_123456",
            questions=[
                ExamQuestion(
                    id="q1",
                    question_text="RAM là viết tắt của cụm từ nào?",
                    options=["Read Access Memory", "Random Access Memory", "Run Action Memory", "Ready Auto Memory"],
                    correct_answer="Random Access Memory",
                    difficulty="de",
                    score=0.25
                )
            ],
            created_at=datetime.utcnow()
        )
    ]

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: str):
    """
    Lấy chi tiết cấu trúc câu hỏi của một đề thi cụ thể.
    """
    return ExamResponse(
        id=exam_id,
        title="Đề thi trắc nghiệm học kỳ I - Tin học 10",
        matrix_id="matrix_mock_789",
        document_id="doc_mock_123456",
        questions=[
            ExamQuestion(
                id="q1",
                question_text="RAM là viết tắt của cụm từ nào?",
                options=["Read Access Memory", "Random Access Memory", "Run Action Memory", "Ready Auto Memory"],
                correct_answer="Random Access Memory",
                difficulty="de",
                score=0.25
            )
        ],
        created_at=datetime.utcnow()
    )

@router.get("/{exam_id}/export")
async def export_exam(exam_id: str, format: str = "pdf"):
    """
    Xuất bản đề thi ra định dạng PDF hoặc DOCX (Word).
    """
    if format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ xuất bản ra định dạng 'pdf' hoặc 'docx'")
    return {
        "exam_id": exam_id,
        "format": format,
        "download_url": f"http://localhost:8000/static/downloads/exam_{exam_id}.{format}"
    }

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(exam_id: str):
    """
    Xóa đề thi khỏi hệ thống.
    """
    return None
