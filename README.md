# AI Chatbot & Exam Generator Backend

Backend API được viết bằng **FastAPI** và **Python 3.11+** dành cho dự án **AI Chatbot sinh đề thi thông minh**. Hệ thống hỗ trợ RAG (Retrieval-Augmented Generation) từ tài liệu và kết nối đa cơ sở dữ liệu (PostgreSQL & MongoDB).

👉 **[HƯỚNG DẪN KHỞI CHẠY CHI TIẾT TỪ A-Z (RUN_GUIDE.md)](RUN_GUIDE.md)**

---

## 🚀 Tính năng chính
* **Người dùng & Xác thực:** Đăng ký, đăng nhập nhận Access Token JWT (OAuth2 Password flow).
* **Quản lý học liệu (RAG):** Hỗ trợ tải lên tài liệu học tập (PDF, DOCX, TXT), phân tích dữ liệu phục vụ sinh câu hỏi AI.
* **Ma trận đề thi:** Thiết lập phân bổ câu hỏi theo độ khó/chủ đề phục vụ cấu trúc đề thi.
* **Sinh đề thi AI:** Tự động sinh đề thi chất lượng cao bằng AI (Gemini / OpenAI) dựa vào tài liệu và ma trận đề.
* **Kiểm tra hệ thống:** Endpoint tĩnh kiểm tra nhanh trạng thái kết nối tới PostgreSQL, MongoDB và hoạt động của server.

---

## 🛠️ Công nghệ sử dụng
* **Core:** [FastAPI](https://fastapi.tiangolo.com/) - Web framework bất đồng bộ.
* **Package Manager:** [uv](https://github.com/astral-sh/uv) - Trình quản lý thư viện siêu tốc độ của Rust.
* **SQL Database:** [PostgreSQL](https://www.postgresql.org/) kết hợp [SQLAlchemy Async](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) (Quản lý migrations).
* **NoSQL Database:** [MongoDB](https://www.mongodb.com/) kết hợp [Motor](https://motor.readthedocs.io/) (Async driver).
* **Containerization:** [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/).

---

## ⚡ Khởi động nhanh bằng Docker (Khuyên dùng)

Để tránh các vấn đề xung đột thư viện hoặc chính sách bảo mật hệ thống trên máy tính của bạn (ví dụ: Windows AppLocker chặn DLL), hãy sử dụng Docker để khởi chạy tất cả dịch vụ.

### 1. Khởi động các container (FastAPI, PostgreSQL, MongoDB)
```bash
docker compose up --build -d
```

### 2. Xem log hoạt động của API Server
```bash
docker compose logs -f web
```

### 3. Xem tài liệu API và dùng thử (Swagger UI)
Khi các dịch vụ đã khởi chạy thành công, truy cập:
* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📂 Cấu trúc thư mục dự án
```text
AiChatbotBackend/
├── app/
│   ├── api/                 # Các router và endpoint API
│   │   └── v1/
│   │       ├── endpoints/   # Định nghĩa logic của từng cụm API
│   │       └── router.py    # Router tổng hợp của v1
│   ├── core/                # Cấu hình dự án, bảo mật, biến môi trường
│   ├── db/                  # Cấu hình cơ sở dữ liệu
│   │   ├── mongodb/         # Kết nối & session MongoDB
│   │   └── postgresql/      # Kết nối & session PostgreSQL (SQLAlchemy)
│   ├── models/              # Định nghĩa các Model database
│   ├── schemas/             # Pydantic schemas (xác thực dữ liệu)
│   ├── services/            # Xử lý logic nghiệp vụ chính (AI, RAG...)
│   └── main.py              # File chạy chính của ứng dụng
├── docs/                    # Tài liệu hướng dẫn dự án
│   └── setup-guide.md       # Tài liệu cài đặt chi tiết cho lập trình viên
├── migrations/              # Các file migration của Alembic (PostgreSQL)
├── docker-compose.yml       # Cấu hình dịch vụ Docker
├── Dockerfile               # File xây dựng Docker image cho FastAPI
├── pyproject.toml           # Định nghĩa thư viện và cấu hình dự án (uv)
└── .env                     # File lưu trữ biến môi trường bảo mật
```

---

## 📖 Tài liệu hướng dẫn lập trình viên khác
Để xem hướng dẫn chi tiết từ lúc clone dự án hoặc các thiết lập môi trường phát triển cục bộ (Local), cấu hình cơ sở dữ liệu, chạy lệnh migration và xử lý lỗi thường gặp, vui lòng tham khảo:
👉 **[Hướng dẫn khởi chạy chi tiết từ A-Z (RUN_GUIDE.md)](RUN_GUIDE.md)**
👉 **[Hướng dẫn cài đặt nhanh cho lập trình viên (setup-guide.md)](file:///d:/Thuc_Tap/Ai_chatbot/AiChatbotBackend/docs/setup-guide.md)**
