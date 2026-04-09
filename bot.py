import os
import asyncio
import random
from datetime import datetime, timedelta
from contextlib import contextmanager

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# НАСТРОЙКИ
# -------------------------
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN не задан!")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL не задана! Проверь Railway Variables")

# фикс PostgreSQL URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("📦 DB CONNECT:", DATABASE_URL)

bot = Bot(token=TOKEN)
dp = Dispatcher()

COOLDOWN = timedelta(minutes=10)

# -------------------------
# БАЗА ДАННЫХ
# -------------------------
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    best = Column(Integer, default=0)
    last_size = Column(Integer, default=0)
    total = Column(Integer, default=0)
    last_time = Column(DateTime)

engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base.metadata.create_all(engine)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        print("❌ DB ERROR:", e)
        raise
    finally:
        session.close()

# -------------------------
# START
# -------------------------
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет 😏\n\n"
        "/ebat — игра\n"
        "/top — топ\n"
        "/me — статистика"
    )

# -------------------------
# ИГРА
# -------------------------
@dp.message(Command("ebat"))
async def ebat_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    now = datetime.now()

    target = None

    # если есть reply — берём цель
    if message.reply_to_message:
        target = message.reply_to_message.from_user.first_name

    with get_session() as session:
        user = session.get(User, user_id)

        # КУЛДАУН
        if user and user.last_time:
            remaining = COOLDOWN - (now - user.last_time)
            if remaining.total_seconds() > 0:
                m = int(remaining.total_seconds() // 60)
                s = int(remaining.total_seconds() % 60)
                await message.reply(f"{username}, подожди {m}м {s}с 😏")
                return

        # ГЕНЕРАЦИЯ
        size = random.randint(1, 20)

        # твой буст
        if user_id == 6824282520 and random.random() < 0.5:
            size = random.randint(50, 200)
        elif random.random() < 0.1:
            size = random.randint(50, 200)

        # СОХРАНЕНИЕ
        if not user:
            user = User(
                user_id=user_id,
                name=username,
                best=size,
                last_size=size,
                total=size,
                last_time=now
            )
            session.add(user)
        else:
            user.last_size = size
            user.last_time = now
            user.best = max(user.best, size)
            user.total += size

    # ОТВЕТ
    if target:
        await message.reply(f"{username} сыграл за {target}: {size} 🍺")
    else:
        await message.reply(f"{username}, ты выпил: {size} 🍺")

# -------------------------
# TOP
# -------------------------
@dp.message(Command("top"))
async def top_handler(message: types.Message):
    with get_session() as session:
        users = session.query(User).order_by(User.total.desc()).limit(10).all()

        text = "🏆 ТОП игроков:\n\n"
        for i, u in enumerate(users, 1):
            text += f"{i}. {u.name} — {u.total} 🍺\n"

    await message.answer(text)

# -------------------------
# ME
# -------------------------
@dp.message(Command("me"))
async def me_handler(message: types.Message):
    user_id = message.from_user.id

    with get_session() as session:
        user = session.get(User, user_id)

        if not user:
            await message.answer("Ты ещё не играл 🤷")
            return

        await message.answer(
            f"📊 Твоя статистика:\n\n"
            f"Последний: {user.last_size} 🍺\n"
            f"Лучший: {user.best} 🍺\n"
            f"Всего: {user.total} 🍺"
        )

# -------------------------
# START BOT
# -------------------------
async def main():
    print("🤖 Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
