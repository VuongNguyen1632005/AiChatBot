from fastapi import APIRouter, status
from sqlalchemy import text
from app.db.postgresql.session import engine
from app.db.mongodb.session import db_mongo

router = APIRouter()

@router.get("/system-status", status_code=status.HTTP_200_OK)
async def get_system_status():
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
