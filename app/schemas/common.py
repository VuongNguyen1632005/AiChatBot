from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")

class ApiErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="Tên trường gặp lỗi (nếu có)")
    message: str = Field(..., description="Thông điệp chi tiết về lỗi")

class ApiResponse(BaseModel, Generic[T]):
    """
    Chuẩn response chung áp dụng cho mọi API của ETECHS.
    """
    success: bool = Field(..., description="Trạng thái thao tác thành công hay thất bại")
    message: str = Field(..., description="Thông điệp mô tả kết quả")
    data: Optional[T] = Field(None, description="Dữ liệu kết quả trả về")
    errors: Optional[List[ApiErrorDetail]] = Field(None, description="Danh sách lỗi chi tiết nếu success=false")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="Thời điểm phản hồi theo chuẩn ISO-8601 UTC"
    )
