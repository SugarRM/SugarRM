import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8328136805:AAFtDSd5r9fn5nbKkdcpvdvVn-zlAIDIUNk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

# 🔹 /ebat
@dp.message(Command("ebat"))
async def ebat_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    today = datetime.now().date()

    if user_id in users and users[user_id]["date"] == today:
        await message.reply(
            f"{username}, ты уже залил сегодя ковбой 😏\n"
            f"Ты залил спермой аляску @lixx3sw: {users[user_id]['last_size']} литров"
        )
        return

    size = random.randint(1, 10)

    if user_id not in users:
        users[user_id] = {
            "name": username,
            "best": size,
            "last_size": size,
            "date": today
        }
    else:
        users[user_id]["last_size"] = size
        users[user_id]["date"] = today

        if size > users[user_id]["best"]:
            users[user_id]["best"] = size

    await message.reply(f"{username}, залил в сладкие дырочки Аляски @lixx3sw: {size} литров спермы 😏")

# 🔹 /top
@dp.message(Command("top"))
async def top_handler(message: types.Message):
    if not users:
        await message.answer("Пока нет данных 🤷")
        return

    # сортировка по лучшему результату
    sorted_users = sorted(users.values(), key=lambda x: x["best"], reverse=True)

    text = "🏆 ТОП игроков:\n\n"

    for i, user in enumerate(sorted_users[:10], start=1):
        text += f"{i}. {user['name']} — {user['best']} л\n"

    await message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())