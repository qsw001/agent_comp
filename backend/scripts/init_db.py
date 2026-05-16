"""
数据库初始化脚本
"""
import asyncio

from sqlalchemy import text

from app.database import engine, Base
from app.config import settings


async def init_database():
    """初始化数据库：创建表"""
    print(f"📦 Connecting to: {settings.DATABASE_URL}")
    print("📋 Creating tables...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized successfully!")


async def check_connection():
    """检查数据库连接"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")


async def main():
    await check_connection()
    await init_database()


if __name__ == "__main__":
    asyncio.run(main())
