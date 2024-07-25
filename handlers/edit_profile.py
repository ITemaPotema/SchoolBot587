from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from usefulfunc.db_commands import update_db, select
from usefulfunc.builder import keyboard_builder


rout_edit = Router()


class EditStates(StatesGroup):
    choose_cat = State()
    edit_cat = State()


@rout_edit.message(Command(commands=["edit_profile"]))
async def say_edit_profile(message: Message, state: FSMContext):
    if select("pupils.db", "pupils", "*", f"WHERE tg_name = '{message.from_user.id}'"):
        keyboard = keyboard_builder(2, "Фото", "Инфо")
        await message.answer(text="Выбери компонент профиля для редактирования:", reply_markup=keyboard)
        await state.set_state(EditStates.choose_cat)
    else:
        await message.answer(text="Ошибка! Скорее всего Вы были заблокированы!")


@rout_edit.callback_query(StateFilter(EditStates.choose_cat))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    if data == "Фото":
        await callback.message.answer(text="Пришли новое фото")
        await state.set_state(EditStates.edit_cat)
    else:
        await callback.message.answer(text="Пришли новый текст профиля")
        await state.set_state(EditStates.edit_cat)
    await state.update_data(choice=data)


@rout_edit.message(StateFilter(EditStates.edit_cat))
async def change_category(message: Message, state: FSMContext):
    data = dict(await state.get_data())
    user = message.from_user.id
    cond = f"WHERE tg_name = '{user}'"
    if data["choice"] == "Фото":
        if message.photo:
            file_id = message.photo[-1].file_id
            update_db("pupils.db", "pupils", "photo", file_id, condition=cond)
            await message.answer(text="Изменения успешно сохранены!")
            await state.clear()
        else:
            await message.answer("Пришли мне ФОТО!")
    else:
        if message.text:
            update_db("pupils.db", "pupils", "info", message.text, condition=cond)
            await message.answer(text="Изменения успешно сохранены!")
            await state.clear()
        else:
            await message.answer(text="Пришли мне текст!")
