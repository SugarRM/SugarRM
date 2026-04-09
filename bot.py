import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8328136805:AAFtDSd5r9fn5nbKkdcpvdvVn-zlAIDIUNk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

COOLDOWN = timedelta(minutes=10)

# 🔹 /start
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


# 🔹 /ebat
@dp.message(Command("ebat"))
async def ebat_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    now = datetime.now()

    if user_id in users:
        last_time = users[user_id]["time"]
        remaining = COOLDOWN - (now - last_time)

        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)

            await message.reply(
                f"{username}, ты уже залил его передохни 😏\n"
                f"Попробовать снова можно через: {minutes} мин {seconds} сек"
            )
            return

    # 🎲 генерация
    size = random.randint(1, 20)

    # шанс на большой результат
    if random.random() < 0.1:
        size = random.randint(50, 200)

    if user_id not in users:
        users[user_id] = {
            "name": username,
            "best": size,
            "last_size": size,
            "time": now
        }
    else:
        users[user_id]["last_size"] = size
        users[user_id]["time"] = now

        if size > users[user_id]["best"]:
            users[user_id]["best"] = size

    await message.reply(f"{username}, ты залил чидори @chidori_offIine: {size} л спермы 😏")


# 🔹 /top
@dp.message(Command("top"))
async def top_handler(message: types.Message):
    if not users:
        await message.answer("Пока нет данных 🤷")
        return

    sorted_users = sorted(users.values(), key=lambda x: x["best"], reverse=True)

    text = "🏆 ТОП игроков:\n\n"

    for i, user in enumerate(sorted_users[:10], start=1):
        text += f"{i}. {user['name']} — {user['best']} л\n"

    await message.answer(text)


# 🔹 /me
@dp.message(Command("me"))
async def me_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Ты ещё не заливал чидори спермой браток 🤷")
        return

    user = users[user_id]

    await message.answer(
        f"📊 Сколько ты залил:\n\n"
        f"Последний результат: {user['last_size']} л\n"
        f"Лучший результат: {user['best']} л"
    )


# 🔹 запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
