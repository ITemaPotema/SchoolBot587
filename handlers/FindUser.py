from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from usefulfunc.db_commands import insert_db, select
from usefulfunc.builder import keyboard_builder
from usefulfunc.finduser_func import back_to_pattern
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
import sqlite3 as sq

rout_find = Router()
bot = Bot(token='6457157815:AAEax-ECU_DegEbtj7p8LjOrXUdtjAFvrdw')


class FindUserStates(StatesGroup):
    letter = State()
    class_lst = State()
    choose_pupil = State()
    decision = State()
    get_message = State()
    unblock = State()


@rout_find.message(Command(commands=["find_user"]))
async def get_find_user(message: Message, state: FSMContext):
    if select("pupils.db", "pupils", "*", f"WHERE tg_name = '{message.from_user.id}'"):
        btn_names = [str(i) for i in range(6, 12)]
        keyboard = keyboard_builder(6, *btn_names)
        await message.answer(text="Выбери параллель:", reply_markup=keyboard)
        await state.set_state(FindUserStates.letter)
    else:
        await message.answer(text="Ошибка! Скорее всего Вы были заблокированы!")
        await state.clear()


@rout_find.callback_query(StateFilter(FindUserStates.letter), lambda cal: cal.data in ("6", "7", "8", "9", "10", "11"))
async def get_letter(callback: CallbackQuery, state: FSMContext):
    keyboard = keyboard_builder(5, "А", "Б", "В", "Г", "Д")
    await callback.message.answer(text="Теперь выбери букву класса", reply_markup=keyboard)
    await state.update_data(paral=callback.data)
    await state.set_state(FindUserStates.class_lst)


@rout_find.callback_query(StateFilter(FindUserStates.class_lst), lambda cal: cal.data in ("А", "Б", "В", "Г", "Д"))
async def get_class_lst(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request = data["paral"]
    cond = f"WHERE grade = '{request}' AND letter = '{callback.data}'"
    info = select("pupils.db", "pupils", ["tg_name", "name", "surname"], condition=cond)
    if info:
        buttons = []
        for tg_name, name, surname in info:
            buttons.append(InlineKeyboardButton(text=f"{name} {surname}", callback_data=f"{tg_name} {name} {surname}"))
        keyboard = InlineKeyboardBuilder()
        keyboard = keyboard.row(*buttons, width=2).as_markup()
        await callback.message.answer(text="Вот список учеников данного класса:", reply_markup=keyboard)
        await state.set_state(FindUserStates.choose_pupil)
    else:
        await callback.message.answer(text="К сожалению в этом классе пока никого нет!")
        await state.clear()


@rout_find.callback_query(StateFilter(FindUserStates.choose_pupil), lambda cal: len(cal.data.split()) == 3)
async def offer_to_send_messages(callback: CallbackQuery, state: FSMContext):
    tg_name, name, surname = callback.data.split()
    await callback.message.answer(text="Вот профиль этого пользователя:")
    cond = f"WHERE tg_name = '{tg_name}'"
    data = select("pupils.db", "pupils", ["*"], condition=cond)[0]
    text = f"""{name} {surname}

{data[7]}"""
    await callback.message.answer(text=text)
    await callback.message.answer_photo(data[3])
    cond = f"WHERE user_id = {callback.from_user.id} AND blocked_id = {tg_name}"
    block_state = select("pupils.db", "blocked_users", ["state"], condition=cond)
    text = block_state[0][0] if block_state else "Заблокировать"
    buttons = [InlineKeyboardButton(text="Написать", callback_data=tg_name),
                  InlineKeyboardButton(text=text, callback_data=text),
                  InlineKeyboardButton(text="Назад", callback_data="Назад"),
                  InlineKeyboardButton(text="Выйти", callback_data="Выйти")]

    keyboard = InlineKeyboardBuilder()
    keyboard = keyboard.row(*buttons, width=2).as_markup()
    await callback.message.answer(text="Выбери действие:", reply_markup=keyboard)
    await state.update_data(receiver=tg_name)
    await state.set_state(FindUserStates.decision)


@rout_find.callback_query(StateFilter(FindUserStates.decision), lambda cal: (cal.data.isdigit() and len(cal.data) > 2) or cal.data == "Выйти")
async def answer_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data.isdigit():
        keyboard = keyboard_builder(1, "Отмена и назад", "Выйти")
        await callback.message.answer(text="Введи сообщение:", reply_markup=keyboard)
        await state.set_state(FindUserStates.get_message)

    else:
        await callback.message.answer(text="Жду новых команд)))")
        await state.clear()


@rout_find.message(StateFilter(FindUserStates.get_message))
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
        await state.set_state(FindUserStates.unblock)

    elif select("pupils.db", "blocked_users", ["*"], condition=cond2):
        await message.answer(text="Вы заблокированы у этого пользователя и не можете послать ему сообщение(((")

    else:
        insert_db("pupils.db", "messages", (receiver, sender, text), columns="(receiver, sender, message)")
        await message.answer(text="Сообщение успешно доставлено!")
        await bot.send_message(text="У вас новое сообщение, проверьте ящик!", chat_id=receiver)
        await state.clear()


@rout_find.callback_query(StateFilter(FindUserStates.get_message), lambda cal: cal.data != "Разблокировать")
async def cancel_sending(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Отменяю отправку!")
    await back_to_pattern(callback, state, FindUserStates)


@rout_find.callback_query(StateFilter(FindUserStates.decision), lambda cal: cal.data == "Назад")
async def back_to(callback: CallbackQuery, state: FSMContext):
    await state.set_state(default_state)
    await back_to_pattern(callback, state, FindUserStates)


@rout_find.callback_query(StateFilter(FindUserStates.decision, FindUserStates.unblock), lambda cal: cal.data in ("Заблокировать", "Разблокировать"))
async def block_user(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    data = await state.get_data()
    blocked_id = dict(data)["receiver"]
    if callback.data == "Заблокировать":
        insert_db("pupils.db", "blocked_users", (user_id, blocked_id, "Разблокировать"))
        await callback.message.answer(text="Пользователь заблокирован!")
    else:
        with sq.connect("pupils.db") as con:
            cur = con.cursor()
            cur.execute(f"""
                    DELETE FROM blocked_users
                    WHERE user_id = '{user_id}' AND blocked_id = '{blocked_id}'
                    """)
            await callback.message.answer(text="Пользователь разблокирован!")
        if await state.get_state() == "FindUserStates:unblock":
            text = dict(data)["text"]
            insert_db("pupils.db", "messages", (blocked_id, callback.from_user.id, text), columns="(receiver, sender, message)")
            await callback.message.answer(text="Сообщение успешно доставлено!")
            await bot.send_message(text="У вас новое сообщение проверьте ящик!", chat_id=blocked_id)
            await state.clear()