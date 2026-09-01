import os
import asyncio
from datetime import datetime

import aiosqlite
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    _pool: asyncpg.Pool | None = None
else:
    _db_path = os.path.join(os.path.dirname(__file__), "data", "bot.db")


async def _get_pg():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool


async def _get_sqlite():
    os.makedirs(os.path.dirname(_db_path), exist_ok=True)
    conn = await aiosqlite.connect(_db_path)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db():
    """Jadvallarni yaratadi (PostgreSQL yoki SQLite)."""
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance BIGINT DEFAULT 0,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS purchases (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    username TEXT,
                    item_type TEXT,
                    amount TEXT,
                    price BIGINT,
                    status TEXT DEFAULT 'pending',
                    txn_id TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                """
            )
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance BIGINT DEFAULT 0"
            )
        return
    conn = await _get_sqlite()
    await conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            item_type TEXT,
            amount TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            txn_id TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """
    )
    await conn.commit()
    await conn.close()


async def add_user(user_id, username, first_name):
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, username, first_name, created_at)
                VALUES ($1,$2,$3,$4)
                ON CONFLICT (id) DO NOTHING
                """,
                user_id, username, first_name, datetime.now().isoformat(),
            )
        return
    conn = await _get_sqlite()
    await conn.execute(
        "INSERT OR IGNORE INTO users (id, username, first_name, created_at) VALUES (?,?,?,?)",
        (user_id, username, first_name, datetime.now().isoformat()),
    )
    await conn.commit()
    await conn.close()


async def add_purchase(user_id, username, item_type, amount, price, txn_id):
    now = datetime.now().isoformat()
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            purchase_id = await conn.fetchval(
                """
                INSERT INTO purchases
                   (user_id, username, item_type, amount, price, txn_id, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                RETURNING id
                """,
                user_id, username, item_type, amount, price, txn_id, now,
            )
        return purchase_id
    conn = await _get_sqlite()
    cur = await conn.execute(
        """INSERT INTO purchases
           (user_id, username, item_type, amount, price, txn_id, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (user_id, username, item_type, amount, price, txn_id, now),
    )
    purchase_id = cur.lastrowid
    await conn.commit()
    await conn.close()
    return purchase_id


async def update_purchase(purchase_id, status):
    now = datetime.now().isoformat()
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE purchases SET status=$1, updated_at=$2 WHERE id=$3",
                status, now, purchase_id,
            )
        return
    conn = await _get_sqlite()
    await conn.execute(
        "UPDATE purchases SET status=?, updated_at=? WHERE id=?",
        (status, now, purchase_id),
    )
    await conn.commit()
    await conn.close()


async def get_purchase(purchase_id):
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM purchases WHERE id=$1", purchase_id)
    conn = await _get_sqlite()
    row = await conn.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,))
    result = await row.fetchone()
    await conn.close()
    return result


async def pending_purchases():
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM purchases WHERE status='pending' ORDER BY id DESC"
            )
    conn = await _get_sqlite()
    row = await conn.execute(
        "SELECT * FROM purchases WHERE status='pending' ORDER BY id DESC"
    )
    result = await row.fetchall()
    await conn.close()
    return result


async def all_users():
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM users ORDER BY id")
    conn = await _get_sqlite()
    row = await conn.execute("SELECT * FROM users ORDER BY id")
    result = await row.fetchall()
    await conn.close()
    return result


async def all_purchases(limit=50):
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM purchases ORDER BY id DESC LIMIT $1", limit
            )
    conn = await _get_sqlite()
    row = await conn.execute(
        "SELECT * FROM purchases ORDER BY id DESC LIMIT ?", (limit,)
    )
    result = await row.fetchall()
    await conn.close()
    return result


async def user_purchases(user_id, limit=10):
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM purchases WHERE user_id=$1 ORDER BY id DESC LIMIT $2",
                user_id, limit,
            )
    conn = await _get_sqlite()
    row = await conn.execute(
        "SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    result = await row.fetchall()
    await conn.close()
    return result


async def get_user(user_id):
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    conn = await _get_sqlite()
    row = await conn.execute("SELECT * FROM users WHERE id=?", (user_id,))
    result = await row.fetchone()
    await conn.close()
    return result


async def get_balance(user_id):
    row = await get_user(user_id)
    if row:
        return row["balance"]
    return 0


async def update_balance(user_id, amount):
    """Balansni o'zgartiradi (amount musbat=qo'shish, manfiy=ayirish)."""
    if DATABASE_URL:
        pool = await _get_pg()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET balance = COALESCE(balance, 0) + $1 WHERE id=$2",
                amount, user_id,
            )
        return
    conn = await _get_sqlite()
    await conn.execute(
        "UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE id=?",
        (amount, user_id),
    )
    await conn.commit()
    await conn.close()