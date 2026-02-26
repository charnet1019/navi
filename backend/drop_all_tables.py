import asyncio
from sqlalchemy import text
from app.database import engine

async def drop_all_tables():
    async with engine.begin() as conn:
        # Execute commands separately
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO navi"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        print("Dropped all tables and recreated schema")

asyncio.run(drop_all_tables())
