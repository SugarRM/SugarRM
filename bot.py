import asyncio
import logging
import os
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramConflictError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, Session

TOKEN = "8328136805:AAFtDSd5r9fn5nbKkdcpvdvVn-zlAIDIUNk"
DB_FILE = "sqlite:////app/data/bot.db"  # Привяжи к persistent 

bot = Bot(token=TOKEN)
dp = Dispatcher()

COOLDOWN = timedelta(minutes=10)

# 🔹 SQLAlchemy
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    best = Column(Integer, default=0)
    last_size = Column(Integer, default=0)
    total = Column(Integer, default=0)
    last_time = Column(DateTime)

os.makedirs('/app/data', exist_ok=True)
engine = create_engine(DB_FILE, echo=False, future=True)
Base.metadata.create_all(engine)
session = Session(engine)

# 🔹 /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    logger.info(f"/start called by user_id={user_id} username={username!r}")
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

# 🔹 /ebat
@dp.message(Command("ebat"))
async def ebat_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    now = datetime.now()
    logger.info(f"/ebat called by user_id={user_id} username={username!r}")

    user = session.get(User, user_id)
    logger.info(f"/ebat DB lookup result for user_id={user_id}: {'found' if user else 'not found'}")

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
            return

    # Генерация литров
    size = random.randint(1, 20)

    # повышенный шанс на супер результат для твоего ID
    if user_id == 6824282520:
        if random.random() < 0.5:  # 50% шанс
            size = random.randint(50, 200)
    else:
        if random.random() < 0.1:  # обычный игрок 10%
            size = random.randint(50, 200)

    # Добавление или обновление пользователя
    if not user:
        user = User(user_id=user_id, name=username, best=size, last_size=size, total=size, last_time=now)
        session.add(user)
        logger.info(f"/ebat creating new user user_id={user_id} username={username!r} size={size}")
    else:
        user.last_size = size
        user.last_time = now
        user.best = max(user.best, size)
        user.total += size  # добавляем литры к суммарному результату
        logger.info(f"/ebat updating user user_id={user_id} size={size} new_total={user.total} new_best={user.best}")

    session.commit()
    logger.info(f"/ebat session.commit() completed for user_id={user_id}")
    await message.reply(f"{username}, ты залил чидори @chidori_offIine: {size} л спермы 😏")



# 🔹 /top
@dp.message(Command("top"))
async def top_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    logger.info(f"/top called by user_id={user_id} username={username!r}")
    users = session.query(User).order_by(User.total.desc()).all()
    logger.info(f"/top DB query returned {len(users)} user(s)")
    if not users:
        await message.answer("Пока нет данных 🤷")
        return

    text = "🏆 ТОП игроков (сумма литров):\n\n"
    for i, user in enumerate(users, start=1):
        text += f"{i}. {user.name} — {user.total} л\n"

    await message.answer(text)

# 🔹 /me
@dp.message(Command("me"))
async def me_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    logger.info(f"/me called by user_id={user_id} username={username!r}")
    user = session.get(User, user_id)
    logger.info(f"/me DB lookup result for user_id={user_id}: {'found' if user else 'not found'}")
    if not user:
        await message.answer("Ты ещё не заливал чидори спермой браток 🤷")
        return

    await message.answer(
        f"📊 Твоя статистика:\n\n"
        f"Последний результат: {user.last_size} л\n"
        f"Лучший результат: {user.best} л\n"
        f"Суммарно залито: {user.total} л"
    )


# 🔹 запуск
async def main():
    logger.info("Bot is starting up")
    while True:

        try:
            logger.info("Starting polling...")
            await dp.start_polling(bot)
        except TelegramConflictError:
            logger.warning("TelegramConflictError: another instance is running. Waiting 15 seconds before retrying...")
            await asyncio.sleep(15)
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Waiting 10 seconds before retrying...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())

