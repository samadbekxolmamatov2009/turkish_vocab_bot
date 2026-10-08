import aiosqlite

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    turkish TEXT NOT NULL,
    uzbek TEXT NOT NULL,
    UNIQUE (level, turkish)
);
CREATE TABLE IF NOT EXISTS stats (
    user_id INTEGER PRIMARY KEY,
    correct INTEGER NOT NULL DEFAULT 0,
    wrong INTEGER NOT NULL DEFAULT 0
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def add_word(level: str, turkish: str, uzbek: str) -> bool:
    """Qo'shildi -> True, allaqachon bor -> False."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT OR IGNORE INTO words (level, turkish, uzbek) VALUES (?, ?, ?)",
            (level, turkish, uzbek),
        )
        await db.commit()
        return cur.rowcount > 0


async def delete_word(word_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM words WHERE id = ?", (word_id,))
        await db.commit()
        return cur.rowcount > 0


async def count_by_level() -> dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT level, COUNT(*) FROM words GROUP BY level")
        return {lvl: n for lvl, n in await cur.fetchall()}


async def list_words(level: str, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, turkish, uzbek FROM words WHERE level = ? ORDER BY id DESC LIMIT ?",
            (level, limit),
        )
        return await cur.fetchall()


async def get_word(word_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, level, turkish, uzbek FROM words WHERE id = ?", (word_id,)
        )
        return await cur.fetchone()


async def random_question(level: str):
    """(word, [3 ta variant]) qaytaradi; variant = (word_id, uzbek). So'z yetmasa None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, turkish, uzbek FROM words WHERE level = ? ORDER BY RANDOM() LIMIT 1",
            (level,),
        )
        word = await cur.fetchone()
        if not word:
            return None
        cur = await db.execute(
            "SELECT id, uzbek FROM words WHERE level = ? AND id != ? AND uzbek != ? "
            "GROUP BY uzbek ORDER BY RANDOM() LIMIT 2",
            (level, word[0], word[2]),
        )
        wrong = await cur.fetchall()
        if len(wrong) < 2:
            return None
        return word, wrong


async def record_answer(user_id: int, is_correct: bool) -> tuple[int, int]:
    col = "correct" if is_correct else "wrong"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (user_id,))
        await db.execute(f"UPDATE stats SET {col} = {col} + 1 WHERE user_id = ?", (user_id,))
        cur = await db.execute("SELECT correct, wrong FROM stats WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        await db.commit()
        return row


async def get_stats(user_id: int) -> tuple[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT correct, wrong FROM stats WHERE user_id = ?", (user_id,))
        return (await cur.fetchone()) or (0, 0)
