# Hướng dẫn Cài đặt và Chạy hệ thống (Setup Guide)

Tài liệu này hướng dẫn chi tiết cách thiết lập môi trường phát triển cục bộ (Local Development) dành cho lập trình viên phát triển Backend của dự án **AI Chatbot & Exam Generator**.

---

## 📋 Điều kiện tiên quyết (Prerequisites)
Đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **Python 3.11+**
2. **Docker & Docker Compose** (Docker Desktop dành cho Windows/Mac)
3. **uv** (Trình quản lý package siêu nhanh cho Python)
   * Cài đặt uv (nếu chưa có): 
     * Windows (PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`
     * Mac/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## ⚙️ Cấu hình biến môi trường
Sao chép file cấu hình mẫu `.env.example` thành file `.env` thực tế:
```bash
cp .env.example .env
```

Mở file `.env` và chỉnh sửa các giá trị cấu hình nếu cần:
```env
# URL kết nối PostgreSQL (sử dụng asyncpg bất đồng bộ)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/my_database

# URL kết nối MongoDB
MONGODB_URL=mongodb://localhost:27017/ai_chatbot

# URL kết nối Redis
REDIS_URL=redis://localhost:6379/0

# URL của ứng dụng Frontend (phục vụ sinh liên kết xác thực email)
FRONTEND_URL=http://localhost:3000

# API Key cho các mô hình ngôn ngữ lớn (Gemini AI)
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🛠️ Hướng dẫn Khởi chạy Hệ thống

### Cách 1: Khởi chạy bằng Docker (Khuyên dùng & Đơn giản nhất)
Khi chạy bằng Docker, toàn bộ mã nguồn FastAPI và các cơ sở dữ liệu sẽ chạy độc lập trong môi trường Linux ảo. Cách này tránh hoàn toàn các lỗi bảo mật trên Windows liên quan đến AppLocker chặn thực thi DLL.

1. **Khởi chạy hệ thống (Build và chạy ngầm):**
   ```bash
   docker compose up --build -d
   ```
2. **Xem nhật ký hoạt động (Log) của FastAPI:**
   ```bash
   docker compose logs -f web
   ```
3. **Mở tài liệu API:**
   Truy cập [http://localhost:8000/docs](http://localhost:8000/docs) trên trình duyệt.

---

### Cách 2: Khởi chạy thủ công ở Local (Chỉ khi không bị Windows chặn)
Nếu bạn không muốn chạy FastAPI qua Docker mà muốn debug trực tiếp ở local:

1. **Khởi chạy riêng PostgreSQL, MongoDB và Redis bằng Docker (chỉ chạy Database):**
   Khởi động các container cơ sở dữ liệu:
   ```bash
   docker compose up -d postgres_db mongodb redis
   ```
2. **Cài đặt thư viện và khởi tạo môi trường ảo (Virtualenv):**
   ```bash
   # Di chuyển vào thư mục dự án chính
   cd AiChatbotBackend
   
   # Đồng bộ thư viện bằng uv
   uv sync
   ```
3. **Khởi chạy FastAPI server ở local:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

*Lưu ý: Nếu gặp lỗi chặn file DLL do chính sách bảo mật Windows (AppLocker/WDAC), hãy cài đặt thư viện vào Python hệ thống và chạy:*
```bash
uv pip install --system -e .
python -m uvicorn app.main:app --reload
```

---

## 🗃️ Hướng dẫn di cư dữ liệu (Database Migrations - Alembic)

Dự án sử dụng **Alembic** để quản lý lịch sử cấu trúc bảng (schema) trong PostgreSQL. Do chính sách bảo mật trên một số máy có thể chặn chạy file `.exe` của Alembic trong thư mục ảo, hãy **luôn gọi Alembic thông qua Python module (`python -m alembic`)**.

### 1. Khởi tạo thư mục migrations (Chỉ chạy 1 lần khi bắt đầu dự án)
Nếu thư mục `migrations` chưa có hoặc bị lỗi rỗng, hãy xóa file `alembic.ini` rỗng và thư mục `migrations` rỗng đi rồi chạy:
```bash
uv run python -m alembic init migrations
```

### 2. Tự động phát hiện thay đổi và tạo file Migration mới (khi bạn thêm/sửa Model)
```bash
uv run python -m alembic revision --autogenerate -m "mô tả thay đổi model"
```

### 3. Cập nhật cấu trúc bảng vào cơ sở dữ liệu PostgreSQL thực tế
```bash
uv run python -m alembic upgrade head
```

---

## 🔍 Kiểm tra sức khỏe hệ thống (Health Check)
Sau khi khởi chạy ứng dụng thành công, truy cập:
👉 **`GET http://localhost:8000/users/system-status`**

Phản hồi mong muốn khi kết nối hoàn toàn thông suốt:
```json
{
  "status": "healthy",
  "services": {
    "server": "healthy",
    "postgresql": "healthy",
    "mongodb": "healthy"
  },
  "errors": null
}
```

---

## 🧪 Hướng dẫn chạy thử nghiệm tự động (Unit Tests)
Dự án tích hợp sẵn bộ kiểm thử tự động sử dụng `pytest` để kiểm tra hoạt động của toàn bộ logic nghiệp vụ (Xác thực, OTP, Đăng ký, Kích hoạt Email, Đặt lại mật khẩu...).

Để chạy toàn bộ các bài kiểm thử:
```bash
uv run pytest
```

---

## ⚠️ Khắc phục một số lỗi thường gặp (Troubleshooting)

### 1. Lỗi: `Attribute "app" not found in module "app.main"`
* **Nguyên nhân:** Bạn đang chạy lệnh khởi chạy trong thư mục con `my_fastapi_project` vốn chứa một file `app/main.py` rỗng.
* **Xử lý:** Di chuyển ra thư mục gốc `AiChatbotBackend` và chạy lệnh tại đó.

### 2. Lỗi: `An Application Control policy has blocked this file`
* **Nguyên nhân:** Chính sách bảo mật Windows Defender Application Control (WDAC) hoặc AppLocker chặn tải file `.exe`/`.pyd` (DLL) bên trong thư mục ảo `.venv`.
* **Xử lý:** Chuyển sang chạy ứng dụng bằng **Docker** (Cách 1) hoặc chạy lệnh thông qua python hệ thống kèm cờ `--system`.

### 3. Lỗi: `Database objects do not implement truth value testing`
* **Nguyên nhân:** Lỗi khi so sánh Boolean đối tượng Database của Motor/PyMongo.
* **Xử lý:** Đã được sửa trong file `app/db/mongodb/session.py`. Đảm bảo sử dụng khối lệnh `try...except` khi lấy database mặc định thay vì dùng toán tử `or`.
