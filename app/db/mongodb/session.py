from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDatabaseSession:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None

    def connect_to_database(self):
        # Thiết lập kết nối Motor Client
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        try:
            # Lấy database mặc định từ URI (nếu có cấu hình trong URL)
            self.db = self.client.get_default_database()
        except Exception:
            # Nếu không cấu hình database mặc định trong URI, dùng database tên là 'ai_chatbot'
            self.db = self.client.get_database("ai_chatbot")

    def close_database_connection(self):
        if self.client:
            self.client.close()

db_mongo = MongoDatabaseSession()