from fastapi import APIRouter, UploadFile, File, Form, status, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    content_type: str
    status: str  # 'processing', 'completed', 'failed'
    created_at: datetime

# Sơ bộ danh sách endpoint tài liệu
@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """
    Tải lên tài liệu học liệu (PDF, Word, TXT) phục vụ sinh đề thi và Chatbot (RAG).
    """
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng file không được hỗ trợ. Chỉ nhận file .pdf, .docx, .txt"
        )
    
    # Mock data phản hồi
    return DocumentResponse(
        id="doc_mock_123456",
        filename=file.filename,
        file_size=1024 * 50,  # 50 KB mock
        content_type=file.content_type,
        status="completed",
        created_at=datetime.utcnow()
    )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents():
    """
    Lấy danh sách các tài liệu đã được tải lên hệ thống.
    """
    return [
        DocumentResponse(
            id="doc_mock_123456",
            filename="tai_lieu_on_tap_tin_hoc.pdf",
            file_size=204850,
            content_type="application/pdf",
            status="completed",
            created_at=datetime.utcnow()
        )
    ]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Lấy chi tiết thông tin và trạng thái xử lý của một tài liệu cụ thể.
    """
    return DocumentResponse(
        id=document_id,
        filename="tai_lieu_on_tap_tin_hoc.pdf",
        file_size=204850,
        content_type="application/pdf",
        status="completed",
        created_at=datetime.utcnow()
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    """
    Xóa tài liệu khỏi hệ thống.
    """
    return None
