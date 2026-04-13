import os
import asyncio
import random
import time
from datetime import datetime, timedelta
from contextlib import contextmanager

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# CONFI
# -------------------------
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN не задан!")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL не задан!")

# фикс Railway URL (иногда старый формат)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("📦 DB:", DATABASE_URL)

bot = Bot(token=TOKEN)
dp = Dispatcher()

COOLDOWN = timedelta(minutes=10)

# -------------------------
# DB
# -------------------------
Base = declarative_base()

BANNED_USERS = [5681014310]  # сюда вставь ID

class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    best = Column(Integer, default=0)
    last_size = Column(Integer, default=0)
    total = Column(Integer, default=0)
    last_time = Column(DateTime)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # 🔥 важно: проверяет живое ли соединение
    pool_recycle=300,
    future=True
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# -------------------------
# SAFE DB INIT (ВАЖНО)
# -------------------------
def init_db():
    for i in range(10):
        try:
            Base.metadata.create_all(engine)
            print("✅ DB READY")
            return
        except Exception as e:
            print(f"⏳ DB not ready ({i+1}/10):", e)
            time.sleep(3)

init_db()

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        print("DB ERROR:", e)
    finally:
        session.close()

# -------------------------
# COMMANDS
# -------------------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет 😏\n\n"
        "/ebat — играть\n"
        "/top — топ\n"
        "/me — статистика"
    )

@dp.message(Command("ebat"))
async def ebat(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    # ❌ блок
    if user_id in BANNED_USERS:
        await message.answer(f"{name}, тебе нельзя только в тебя 😏")
        return

@dp.message(Command("ebat"))
async def ebat(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    now = datetime.now()

    with get_session() as session:
        user = session.get(User, user_id)

        # cooldown
        if user and user.last_time:
            diff = COOLDOWN - (now - user.last_time)
            if diff.total_seconds() > 0:
                await message.reply(f"стоять ковбой ты уже залил в чидори {int(diff.total_seconds())} сек 😏")
                return

        # result
        size = random.randint(1, 20)

        if user_id == 6824282520 and random.random() < 0.5:
            size = random.randint(50, 200)

        # save
        if not user:
            user = User(
                user_id=user_id,
                name=name,
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

    await message.answer(f"{name}:ты залил Чидори {size} литров спермы 😏")

@dp.message(Command("top"))
async def top(message: types.Message):
    with get_session() as session:
        users = session.query(User).order_by(User.total.desc()).limit(10).all()

    text = "🏆 топ кто больше залил спермы в чидори:\n\n"
    for i, u in enumerate(users, 1):
        text += f"{i}. {u.name} — {u.total}\n"

    await message.answer(text)

@dp.message(Command("me"))
async def me(message: types.Message):
    user_id = message.from_user.id

    with get_session() as session:
        user = session.get(User, user_id)

    if not user:
        await message.answer("Ты ещё не играл")
        return

    await message.answer(
        f"📊 Ты:\n"
        f"Последний: {user.last_size}\n"
        f"Лучший: {user.best}\n"
        f"Всего: {user.total}"
    )

# -------------------------
# START BOT
# -------------------------
async def main():
    print("🤖 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
