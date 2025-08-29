"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
from typing import Dict, List, Optional, Tuple

import aiosqlite
import orjson
from redbot.core.data_manager import cog_data_path


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.data_path = cog_data_path(raw_name="EasterHunt")
        self.db_path = self.data_path / "easterhunt.db"
        self.conn = None

    async def initialize(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.create_tables()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def create_tables(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                shards INTEGER DEFAULT 0,
                gems INTEGER DEFAULT 0,
                last_hunt REAL DEFAULT 0,
                last_work REAL DEFAULT 0,
                last_daily REAL DEFAULT 0,
                last_give REAL DEFAULT 0,
                active_hunt INTEGER DEFAULT 0,
                active_work INTEGER DEFAULT 0,
                hunt_streak INTEGER DEFAULT 0,
                last_hunt_time REAL DEFAULT 0,
                pity_counter_json TEXT DEFAULT '{}',
                achievements_json TEXT DEFAULT '{}'
            )""",
            """CREATE TABLE IF NOT EXISTS user_eggs (
                user_id INTEGER,
                egg_type TEXT,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, egg_type),
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS egg_images (
                egg_type TEXT PRIMARY KEY,
                image_url TEXT
            )""",
        ]
        async with self.conn.cursor() as cursor:
            for query in queries:
                await cursor.execute(query)
            await self.conn.commit()

    async def ensure_user(self, user_id: int):
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if not await cursor.fetchone():
                await cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await self.conn.commit()

    async def get_user_field(self, user_id: int, field: str):
        await self.ensure_user(user_id)
        async with self.conn.cursor() as cursor:
            await cursor.execute(f"SELECT {field} FROM users WHERE user_id = ?", (user_id,))
            return (await cursor.fetchone())[0]

    async def set_user_field(self, user_id: int, field: str, value):
        if field in ["active_hunt", "active_work"]:
            value = 1 if value else 0
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                f"UPDATE users SET {field} = ? WHERE user_id = ?",
                (value, user_id),
            )
        await self.conn.commit()

    async def get_eggs(self, user_id: int) -> Dict[str, int]:
        await self.ensure_user(user_id)
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT egg_type, count FROM user_eggs WHERE user_id = ?", (user_id,)
            )
            rows = await cursor.fetchall()
            eggs = {"common": 0, "silver": 0, "gold": 0, "shiny": 0, "legendary": 0, "mythical": 0}
            eggs.update(dict(rows))
            return eggs

    async def get_egg_count(self, user_id: int, egg_type: str) -> int:
        await self.ensure_user(user_id)
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT count FROM user_eggs WHERE user_id = ? AND egg_type = ?",
                (user_id, egg_type),
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def set_egg_count(self, user_id: int, egg_type: str, value: int):
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "INSERT OR REPLACE INTO user_eggs (user_id, egg_type, count) VALUES (?, ?, ?)",
                (user_id, egg_type, value),
            )
        await self.conn.commit()

    async def get_pity_counters(self, user_id: int) -> Dict[str, int]:
        json_str = await self.get_user_field(user_id, "pity_counter_json")
        return orjson.loads(json_str)

    async def set_pity_counters(self, user_id: int, data: Dict[str, int]):
        await self.set_user_field(user_id, "pity_counter_json", json.dumps(data))

    async def get_achievements(self, user_id: int) -> Dict[str, bool]:
        json_str = await self.get_user_field(user_id, "achievements_json")
        return orjson.loads(json_str)

    async def set_achievements(self, user_id: int, data: Dict[str, bool]):
        await self.set_user_field(user_id, "achievements_json", json.dumps(data))

    async def get_egg_images(self) -> Dict[str, str]:
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT egg_type, image_url FROM egg_images")
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows if row[1] is not None}

    async def set_egg_image(self, egg_type: str, url: Optional[str]):
        async with self.conn.cursor() as cursor:
            if url is None:
                await cursor.execute("DELETE FROM egg_images WHERE egg_type = ?", (egg_type,))
            else:
                await cursor.execute(
                    "INSERT OR REPLACE INTO egg_images (egg_type, image_url) VALUES (?, ?)",
                    (egg_type, url),
                )
        await self.conn.commit()

    async def delete_user_data(self, user_id: int):
        async with self.conn.cursor() as cursor:
            await cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def get_stale_active_users(self) -> List[Tuple[int, float]]:
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT user_id, last_work FROM users WHERE active_work = 1")
            return await cursor.fetchall()

    async def get_user_count(self) -> int:
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM users")
            return (await cursor.fetchone())[0]

    async def reset_all(self):
        async with self.conn.cursor() as cursor:
            await cursor.execute("DELETE FROM users")
            await cursor.execute("DELETE FROM egg_images")
        await self.conn.commit()

    async def get_leaderboard_data(self) -> List[Tuple[int, int]]:
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT user_id, SUM(count) as total
                FROM user_eggs
                WHERE egg_type IN ('common', 'silver', 'gold')
                GROUP BY user_id
                HAVING total > 0
                ORDER BY total DESC
                """
            )
            return await cursor.fetchall()
