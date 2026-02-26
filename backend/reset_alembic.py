import asyncio
from sqlalchemy import text
from app.database import engine

async def reset_alembic():
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        print("Dropped alembic_version table")

asyncio.run(reset_alembic())
