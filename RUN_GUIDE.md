# 🚀 Hướng Dẫn Khởi Chạy Dự Án (Từ A đến Z)

Tài liệu này hướng dẫn chi tiết các bước để tải mã nguồn, cấu hình môi trường và khởi chạy hệ thống **AI Chatbot & Exam Generator Backend** từ khi bắt đầu clone repo về máy.

---

## 📋 Điều kiện tiên quyết (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **Git** (để clone dự án)
2. **Docker & Docker Compose** (để chạy database và toàn bộ ứng dụng nhanh nhất)
3. *(Tùy chọn)* **Python 3.11+** và **uv** (nếu muốn chạy trực tiếp trên môi trường local không qua Docker)

---

## 🛠️ Quy trình các bước thực hiện

### Bước 1: Clone Repository về máy
Mở Terminal/PowerShell và chạy lệnh sau để tải mã nguồn về máy:
```bash
git clone <URL_REPOS_CUA_BAN>
```
Sau đó di chuyển vào thư mục của dự án:
```bash
cd AiChatbotBackend
```

---

### Bước 2: Cấu hình biến môi trường (`.env`)
Dự án sử dụng file `.env` để cấu hình kết nối database, các API Key và cấu hình hệ thống khác. 

1. Tạo file `.env` bằng cách sao chép từ file mẫu:
   ```bash
   cp .env.example .env
   ```
   *(Trên Windows PowerShell, nếu lệnh `cp` không hoạt động, sử dụng: `copy .env.example .env`)*

2. Mở file `.env` vừa tạo và điền đầy đủ các thông tin:
   * **`DATABASE_URL`**: URL kết nối PostgreSQL (mặc định đã được cấu hình trỏ tới container database).
   * **`MONGODB_URL`**: URL kết nối MongoDB.
   * **`REDIS_URL`**: URL kết nối Redis.
   * **`GEMINI_API_KEY`**: Điền API Key của Gemini để sử dụng tính năng AI sinh đề thi.

> [!IMPORTANT]
> Tuyệt đối không được commit file `.env` chứa thông tin bảo mật/API Key lên GitHub. File này đã được thêm vào `.gitignore`.

---

### Bước 3: Khởi chạy ứng dụng

Bạn có thể lựa chọn 1 trong 2 cách khởi chạy dưới đây:

#### Cách 1: Khởi chạy bằng Docker Compose (Khuyên dùng 🌟)
Cách này là đơn giản nhất, tự động dựng tất cả cơ sở dữ liệu (Postgres, MongoDB, Redis) cùng với Backend FastAPI trong một môi trường cô lập, tránh lỗi xung đột hệ điều hành.

1. **Khởi động các container:**
   ```bash
   docker compose up --build -d
   ```
2. **Theo dõi log hoạt động của backend API:**
   ```bash
   docker compose logs -f web
   ```
3. **Mở tài liệu API:**
   Sau khi container khởi chạy thành công, truy cập trình duyệt tại địa chỉ:
   * **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) (Dùng thử các API trực tiếp)
   * **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

#### Cách 2: Khởi chạy trực tiếp tại Local (Dành cho lập trình viên phát triển/debug)
Nếu bạn muốn chạy trực tiếp FastAPI ở máy local để tiện chỉnh sửa code và debug nhanh:

1. **Chạy các cơ sở dữ liệu nền bằng Docker (chỉ chạy Database và Redis):**
   ```bash
   docker compose up -d postgres_db mongodb redis
   ```
   
2. **Cài đặt công cụ quản lý thư viện `uv` (nếu chưa có):**
   * **Windows (PowerShell):**
     ```powershell
     irm https://astral.sh/uv/install.ps1 | iex
     ```
   * **Mac/Linux:**
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```

3. **Cài đặt thư viện và thiết lập môi trường ảo:**
   ```bash
   uv sync
   ```

4. **Chạy lệnh cập nhật cấu trúc database (Alembic Migrations):**
   ```bash
   uv run python -m alembic upgrade head
   ```

5. **Khởi chạy ứng dụng FastAPI:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```
   *Lưu ý cho Windows:* Nếu gặp lỗi chính sách bảo mật chặn file thực thi `.exe` trong môi trường ảo (AppLocker), hãy chạy thông qua Python hệ thống:
   ```bash
   uv pip install --system -e .
   python -m uvicorn app.main:app --reload
   ```

---

## 🔍 Bước 4: Kiểm tra sức khỏe hệ thống (Health Check)

Để chắc chắn rằng backend đã kết nối thành công tới cả PostgreSQL và MongoDB, hãy truy cập đường dẫn sau trên trình duyệt hoặc gửi request GET:
👉 **[http://localhost:8000/users/system-status](http://localhost:8000/users/system-status)**

Phản hồi mong muốn (Trạng thái khỏe mạnh):
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

## 🧪 Bước 5: Chạy các bài kiểm thử tự động (Unit Tests)

Dự án tích hợp sẵn bộ kiểm thử tự động bằng `pytest`. Để chạy kiểm tra xem toàn bộ các chức năng xác thực, OTP, đổi mật khẩu... hoạt động bình thường hay không:

* Chạy test trên local:
  ```bash
  uv run pytest
  ```
* Chạy test bên trong container Docker:
  ```bash
  docker compose exec web uv run pytest
  ```

---

## ⚠️ Xử lý một số sự cố thường gặp (Troubleshooting)

| Vấn đề | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **Cổng 5432 hoặc 27017 đã bị chiếm dụng** | Có một service Postgres/MongoDB khác đang chạy ngầm trên máy của bạn. | Tạm dừng các service đó hoặc sửa lại cổng ở cột bên trái phần `ports` trong file `docker-compose.yml`. |
| **Không kết nối được cơ sở dữ liệu** | Các container database chưa sẵn sàng hoàn toàn hoặc biến môi trường sai. | Chạy `docker compose restart web` để API kết nối lại sau khi các DB đã khởi động xong. |
| **Lỗi `AppLocker` / Chặn file `.exe` trên Windows** | Windows Defender Application Control chặn chạy script từ `.venv`. | Dùng **Cách 1 (Docker Compose)** để chạy ứng dụng trong container Linux. |

---
*Chúc bạn chạy dự án thành công! Nếu gặp bất kỳ khó khăn nào, hãy liên hệ với đội ngũ phát triển.*
