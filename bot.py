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
# Настройки
# -------------------------
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN не задан!")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

COOLDOWN = timedelta(minutes=10)

# -------------------------
# База данных
# -------------------------
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

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
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# -------------------------
# Команды
# -------------------------
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    username = message.from_user.first_name
    text = (
        f"Привет, {username} 😏\n\n"
        "🎮 Команды:\n"
        "/ebat — сыграть\n"
        "/ebat @user — сыграть за другого\n"
        "/top — топ игроков\n"
        "/me — твоя статистика\n"
    )
    await message.answer(text)

@dp.message(Command("ebat"))
async def ebat_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    now = datetime.now()

    target_name = None

    # --- ищем цель через @username ---
    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                target_name = message.text[ent.offset:ent.offset + ent.length]

    # --- если ответ на сообщение ---
    if message.reply_to_message:
        target_name = message.reply_to_message.from_user.first_name

    with get_session() as session:
        user = session.get(User, user_id)

        # кулдаун
        if user and user.last_time:
            remaining = COOLDOWN - (now - user.last_time)
            if remaining.total_seconds() > 0:
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)
                await message.reply(
                    f"{username}, подожди {minutes}м {seconds}с 😏"
                )
                return

        # генерация результата
        size = random.randint(1, 20)

        if user_id == 6824282520:
            if random.random() < 0.5:
                size = random.randint(50, 200)
        else:
            if random.random() < 0.1:
                size = random.randint(50, 200)

        # обновление БД
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

    # --- ответ ---
    if target_name:
        await message.reply(
            f"{username} сыграл за {target_name}: {size} 😏"
        )
    else:
        await message.reply(
            f"{username}, результат: {size} 😏"
        )

@dp.message(Command("top"))
async def top_handler(message: types.Message):
    with get_session() as session:
        users = session.query(User).order_by(User.total.desc()).limit(10).all()

        if not users:
            await message.answer("Пока нет данных 🤷")
            return

        text = "🏆 ТОП игроков:\n\n"
        for i, user in enumerate(users, start=1):
            text += f"{i}. {user.name} — {user.total}\n"

    await message.answer(text)

@dp.message(Command("me"))
async def me_handler(message: types.Message):
    user_id = message.from_user.id

    with get_session() as session:
        user = session.get(User, user_id)

        if not user:
            await message.answer("Ты ещё не играл 🤷")
            return

        text = (
            f"📊 Твоя статистика:\n\n"
            f"Последний: {user.last_size}\n"
            f"Лучший: {user.best}\n"
            f"Всего: {user.total}"
        )

    await message.answer(text)

# -------------------------
# Запуск
# -------------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
