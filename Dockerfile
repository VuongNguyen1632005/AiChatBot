FROM python:3.11-slim

# Giúp hiển thị log print() ngay lập tức trong Docker
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt các công cụ cần thiết cho compile và python-dev nếu cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt uv để tăng tốc độ cài thư viện
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Sao chép các file cấu hình dependency trước
COPY pyproject.toml uv.lock* ./

# Thực hiện sync thư viện (không dùng virtualenv bên trong docker slim)
RUN uv pip install --system --no-cache -r pyproject.toml

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Expose cổng 8000
EXPOSE 8000

# Khởi chạy server FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
