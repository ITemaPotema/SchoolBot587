from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
import sqlite3 as sq
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from usefulfunc.builder import keyboard_builder
from usefulfunc.db_commands import select, insert_db


rout_mail = Router()
bot = Bot(token='your token here')


class MailStates(StatesGroup):
    ready_to_answer = State()
    answer = State()
    unblock = State()


async def get_mails(message):
    with sq.connect("pupils.db") as con:
        cur = con.cursor()
        receiver = message.from_user.id

        cur.execute(f"""
                    SELECT name, surname, message, grade, letter, messages.sender
                    FROM pupils JOIN messages ON pupils.tg_name = messages.sender
                    WHERE messages.receiver = '{receiver}' 
                    """)
        data = cur.fetchall()
        cur.execute(f"""
        DELETE FROM messages
        WHERE receiver = '{receiver}'
        """)
    return data


@rout_mail.message(Command(commands=["my_mail_box"]))
async def watch_my_mails(message: Message, state: FSMContext):
    data = await get_mails(message)
    if data:
        for name, surname, mes, grade, letter, sender in data:
            button = InlineKeyboardButton(text="Ответить", callback_data=sender)
            keyboard = InlineKeyboardBuilder()
            keyboard = keyboard.row(button, width=1).as_markup()
            await message.answer(text=f"От {name} {surname} {grade}{letter}")
            if mes.split()[-1] == "sticker":
                await message.answer_sticker(f"{mes.split()[0]}", reply_markup=keyboard)
            elif mes.split()[-1] == "photo":
                await message.answer_photo(f"{mes.split()[0]}", reply_markup=keyboard)
            else:
                await message.answer(text=mes, reply_markup=keyboard)
            await state.set_state(MailStates.ready_to_answer)
    else:
        await message.answer(text="Пока здесь ничего нет(")


@rout_mail.callback_query(StateFilter(MailStates.ready_to_answer), lambda cal: cal.data.isdigit() and len(cal.data) > 2)
async def answer_message(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Введи сообщение:")
    await state.update_data(receiver=callback.data)
    await state.set_state(MailStates.answer)


@rout_mail.message(StateFilter(MailStates.answer))
async def save_message_to_mailbox(message: Message, state: FSMContext):
    receiver = await state.get_data()
    receiver = dict(receiver)["receiver"]
    sender = message.from_user.id
    if message.sticker:
        text = message.sticker.file_id + " sticker"
    elif message.photo:
        text = message.photo[-1].file_id + " photo"
    else:
        text = message.text

    cond1 = f"WHERE user_id = {sender} AND blocked_id = {receiver}"
    cond2 = f"WHERE user_id = {receiver} AND blocked_id = {sender}"
    if select("pupils.db", "blocked_users", ["*"], condition=cond1):
        keyboard = keyboard_builder(1, "Разблокировать")
        await message.answer(text="Этот пользователь заблокирован, сначала разблокируйте его, чтобы отправить сообщение!",
        reply_markup=keyboard)
        await state.update_data(receiver=receiver, text=text)
        await state.set_state(MailStates.unblock)

    elif select("pupils.db", "blocked_users", ["*"], condition=cond2):
        await message.answer(text="Вы заблокированы у этого пользователя и не можете послать ему сообщение(((")

    else:
        insert_db("pupils.db", "messages", (receiver, sender, text), columns="(receiver, sender, message)")
        await message.answer(text="Сообщение успешно доставлено!")
        await bot.send_message(text="У вас новое сообщение, проверьте ящик!", chat_id=receiver)
        await state.clear()

