from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (SessionPasswordNeededError,
                             PhoneNumberBannedError, PhoneCodeInvalidError,
                             PhoneCodeExpiredError)
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import threading
import functools

api_id = 25217515
api_hash = "1bb27e5be73593e33fc735c1fbe0d855"
bot_token = "7229675132:AAHDvs6KnAvNEQf10lEw9e9-O64L9k7objg"

loop = asyncio.new_event_loop()
thread = threading.Thread(target=loop.run_forever, daemon=True)
thread.start()

bot = telebot.TeleBot(bot_token)
user_states = {}


def run_async(coro):

    def wrapper(*args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(coro(*args, **kwargs), loop)
        return future.result()

    return wrapper


class S1:

    def __init__(self):
        self.client = None

    @run_async
    async def connect(self, phone):
        self.client = TelegramClient(StringSession(),
                                     api_id,
                                     api_hash,
                                     loop=loop)
        await self.client.connect()
        await self.client.send_code_request(phone)
        return self.client

    @run_async
    async def sign_in(self, code):
        return await self.client.sign_in(code=code)

    @run_async
    async def sign_in_password(self, password):
        return await self.client.sign_in(password=password)

    @run_async
    async def disconnect(self):
        await self.client.disconnect()
        self.client = None

    @run_async
    async def is_authorized(self):
        return await self.client.is_user_authorized()

    @property
    def session(self):
        return self.client.session.save() if self.client else None


@bot.message_handler(commands=["start"])
def start(message):
    markup = InlineKeyboardMarkup(row_width=1)
    btn_start = InlineKeyboardButton("بدء استخراج جلسة telethon",
                                     callback_data="start_session")
    btn_channel = InlineKeyboardButton("DEF", url="https://t.me/jokerpython3")
    markup.add(btn_start, btn_channel)
    bot.send_message(message.chat.id,
                     "هذا بوت استخراج كود سيشن ال telethin",
                     parse_mode="Markdown",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "start_session")
def request_phone(call):
    user_states[call.from_user.id] = {"step": "phone", "client": S1()}
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="دز وقمك مع رمز دولة مثال  +96477####")


@bot.message_handler(func=lambda message: user_states.get(
    message.from_user.id, {}).get("step") == "phone")
def handle_phone(message):
    try:
        user_data = user_states[message.from_user.id]
        phone = message.text
        user_data["client"].connect(phone)
        user_data["step"] = "code"
        bot.send_message(message.chat.id,
                         "دز كود تحقق مع مسافات يعني هيج 7 6 7 9 0")

    except PhoneNumberBannedError:
        bot.send_message(message.chat.id, "⛔ هذا الرقم محظور من التليجرام")
        del user_states[message.from_user.id]
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ: {str(e)}")
        del user_states[message.from_user.id]


@bot.message_handler(func=lambda message: user_states.get(
    message.from_user.id, {}).get("step") == "code")
def handle_code(message):
    user_data = user_states[message.from_user.id]
    code = message.text.strip()

    try:
        user_data["client"].sign_in(code)

        if user_data["client"].is_authorized():
            session_str = user_data["client"].session
            bot.send_message(message.chat.id,
                             f"✅ تم إنشاء الجلسة بنجاح:\n`{session_str}`",
                             parse_mode="Markdown")
            user_data["client"].disconnect()
            del user_states[message.from_user.id]
        else:
            bot.send_message(message.chat.id, "❌ فشل في تسجيل الدخول")

    except SessionPasswordNeededError:
        user_data["step"] = "password"
        bot.send_message(message.chat.id, "دز باسورد حسابك")
    except (PhoneCodeInvalidError, PhoneCodeExpiredError):
        bot.send_message(message.chat.id,
                         "⛔ كود التحقق غير صحيح أو منتهي الصلاحية")
        del user_states[message.from_user.id]
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ: {str(e)}")
        del user_states[message.from_user.id]


@bot.message_handler(func=lambda message: user_states.get(
    message.from_user.id, {}).get("step") == "password")
def handle_password(message):
    user_data = user_states[message.from_user.id]
    password = message.text

    try:
        user_data["client"].sign_in_password(password)

        if user_data["client"].is_authorized():
            session_str = user_data["client"].session
            bot.send_message(message.chat.id,
                             f"✅ تم إنشاء الجلسة بنجاح:\n`{session_str}`",
                             parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ فشل في تسجيل الدخول")

    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ: {str(e)}")
    finally:
        user_data["client"].disconnect()
        del user_states[message.from_user.id]


if __name__ == "__main__":
    bot.polling(none_stop=True)
