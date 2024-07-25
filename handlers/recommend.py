from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from usefulfunc.db_commands import select, insert_db
from usefulfunc.builder import keyboard_builder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3 as sq
import asyncio

recommend_rout = Router()
bot: Bot = Bot(token='your token here')


class TypeMessage(StatesGroup):
    start_choice = State()
    start = State()
    type_message = State()


@recommend_rout.message(Command(commands=["recommendations"]))
async def call_recommend(message: Message, state: FSMContext):
    await message.answer(text="Это лента из учеников нашей гимназии, у которых такие же интересы как и у тебя!")
    keyboard = keyboard_builder(2, "Начать", "Отмена")
    await message.answer(text="Начинаем?", reply_markup=keyboard)
    await state.set_state(TypeMessage.start_choice)


def recommend_profiles(my_interests, pupils_lst, i=0):
    if i >= len(pupils_lst):
        i = 0
    while i < len(pupils_lst):
        recommend_profile = pupils_lst[i]
        text = recommend_profile[-2] + my_interests
        if len(set(text)) < len(text):
            return recommend_profile, i
        i += 1


def func(callback):
    tg_id = callback.from_user.id
    cond0 = f"WHERE tg_name = '{tg_id}'"
    my_interests = select("pupils.db", "pupils", ["interests"], condition=cond0)
    cond1 = f"WHERE tg_name != {tg_id}"
    pupils_lst = select("pupils.db", "pupils", "*", cond1)
    return my_interests[0][0], pupils_lst, str(tg_id)


@recommend_rout.callback_query(lambda cal: cal.data in ("Начать", "Отмена"), StateFilter(TypeMessage.start_choice))
async def answer_kb_option(callback: CallbackQuery, state: FSMContext):
    loop = asyncio.get_event_loop()
    if callback.data == "Начать":
        if select("pupils.db", "pupils", "*", f"WHERE tg_name = '{callback.from_user.id}'"):
            my_interests, pupils_lst, tg_id = await loop.run_in_executor(None, func, callback)
            profile, i = await loop.run_in_executor(None, recommend_profiles, my_interests, pupils_lst)
            if profile:
                text = f"""           
{profile[1]} {str(profile[4]) + profile[5]} 

{profile[7]}"""
                keyboard = keyboard_builder(2, "Написать", "Далее")
                await callback.message.answer(text=text)
                await callback.message.answer_photo(profile[3], reply_markup=keyboard)
                await state.update_data(receiver=profile[0], i=i + 1)
                await state.set_state(TypeMessage.start)
            else:
                await callback.message.answer(text="С вашими интересами никого нет(")
                await state.clear()
        else:
            await callback.message.answer(text="Ошибка! Скорее всего Вы были заблокированы!")
            await state.clear()
    else:
        await callback.message.answer(text="До встречи!")
        await state.clear()


@recommend_rout.callback_query(lambda cal: cal.data in ("Далее", "Написать"), StateFilter(TypeMessage.start))
async def recommend_action(callback: CallbackQuery, state: FSMContext):
    loop = asyncio.get_event_loop()
    try:
        if callback.data == "Далее":
            my_interests, pupils_lst, tg_id = await loop.run_in_executor(None, func, callback)
            data = await state.get_data()
            ind = data["i"]
            profile, i = await loop.run_in_executor(None, recommend_profiles, my_interests, pupils_lst, ind)
            text = f"""{profile[1]} {str(profile[4]) + profile[5]}
{profile[7]}"""
            keyboard = keyboard_builder(2, "Написать", "Далее")
            await callback.message.answer(text=text)
            await callback.message.answer_photo(profile[3], reply_markup=keyboard)
            await state.update_data(receiver=profile[0], i=i+1)

        else:
            await callback.message.answer(text="Введи сообщение:")
            await state.set_state(TypeMessage.type_message)

    except:
        pass


@recommend_rout.message(StateFilter(TypeMessage.type_message))
async def send_message(message: Message, state: FSMContext):
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
        await message.answer(
            text="Этот пользователь заблокирован, сначала разблокируйте его, чтобы отправить сообщение!",
            reply_markup=keyboard)
        await state.update_data(receiver=receiver, text=text)

    elif select("pupils.db", "blocked_users", ["*"], condition=cond2):
        await message.answer(text="Вы заблокированы у этого пользователя и не можете послать ему сообщение(((")

    else:
        insert_db("pupils.db", "messages", (receiver, sender, text), columns="(receiver, sender, message)")
        await message.answer(text="Сообщение успешно доставлено!")
        await bot.send_message(text="У вас новое сообщение, проверьте ящик!", chat_id=receiver)
        await state.clear()


@recommend_rout.callback_query(lambda cal: cal.data in "Разблокировать", StateFilter(TypeMessage.type_message))
async def block_user(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    data = await state.get_data()
    blocked_id = dict(data)["receiver"]
    text = dict(data)["text"]
    with sq.connect("pupils.db") as con:
        cur = con.cursor()
        cur.execute(f"""
                DELETE FROM blocked_users
                WHERE user_id = '{user_id}' AND blocked_id = '{blocked_id}'
                """)
    await callback.message.answer(text="Пользователь разблокирован!")
    insert_db("pupils.db", "messages", (blocked_id, user_id, text), columns="(receiver, sender, message)")
    await callback.message.answer(text="Сообщение успешно доставлено!")
    await bot.send_message(text="У вас новое сообщение, проверьте ящик!", chat_id=blocked_id)
    await state.clear()


