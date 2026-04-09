import os
import asyncio
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# Настройки
# -------------------------
# Берём токен бота из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN не задан!")

# URL подключения к PostgreSQL через Railway TCP proxy
DATABASE_PUBLIC_URL = os.getenv("DATABASE_PUBLIC_URL")
if not DATABASE_PUBLIC_URL:
    raise Exception("DATABASE_PUBLIC_URL не задана!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

COOLDOWN = timedelta(minutes=10)

# -------------------------
# Настройка базы данных
# -------------------------
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(BigInteger, primary_key=True)        # Telegram ID
    name = Column(String, nullable=False)               # Имя
    best = Column(Integer, default=0)                   # Лучший результат
    last_size = Column(Integer, default=0)              # Последний результат
    total = Column(Integer, default=0)                  # Суммарно залито
    last_time = Column(DateTime)                         # Время последнего заливания

# Создаём движок и сессию
engine = create_engine(DATABASE_PUBLIC_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

# Создаём таблицы, если их нет
Base.metadata.create_all(engine)

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
        "/top — топ игроков\n"
        "/me — твоя статистика\n\n"
        "💸 Донат (TON):\n"
        "`UQB6PcolhwqGLhbdQQoRdBOpoROTYSVR8KqnbYWumzxmDxI9`\n\n"
        "Спасибо за поддержку ❤️"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("ebat"))
async def ebat_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    now = datetime.now()

    session = SessionLocal()
    user = session.get(User, user_id)

    # Проверка кулдауна
    if user and user.last_time:
        remaining = COOLDOWN - (now - user.last_time)
        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            await message.reply(
                f"{username}, ты уже залил его 😏\n"
                f"Попробовать снова можно через: {minutes} мин {seconds} сек"
            )
            session.close()
            return

    # Генерация литров
    size = random.randint(1, 20)

    # Шанс на супер результат для твоего ID
    if message.from_user.id == 6824282520:  # <- твой Telegram ID
        if random.random() < 0.5:
            size = random.randint(50, 200)
    else:
        if random.random() < 0.1:
            size = random.randint(50, 200)

    # Добавляем или обновляем пользователя
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

    session.commit()
    session.close()

    await message.reply(f"{username}, ты залил чидори @chidori_offIine: {size} л спермы 😏")

@dp.message(Command("top"))
async def top_handler(message: types.Message):
    session = SessionLocal()
    users = session.query(User).order_by(User.total.desc()).limit(10).all()
    session.close()

    if not users:
        await message.answer("Пока нет данных 🤷")
        return

    text = "🏆 ТОП игроков (сумма литров):\n\n"
    for i, user in enumerate(users, start=1):
        text += f"{i}. {user.name} — {user.total} л\n"

    await message.answer(text)

@dp.message(Command("me"))
async def me_handler(message: types.Message):
    user_id = message.from_user.id
    session = SessionLocal()
    user = session.get(User, user_id)
    session.close()

    if not user:
        await message.answer("Ты ещё не заливал чидори спермой браток 🤷")
        return

    await message.answer(
        f"📊 Твоя статистика:\n\n"
        f"Последний результат: {user.last_size} л\n"
        f"Лучший результат: {user.best} л\n"
        f"Суммарно залито: {user.total} л"
    )

# -------------------------
# Запуск
# -------------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
