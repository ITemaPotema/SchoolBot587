from aiogram import Router
from aiogram.types import Message, CallbackQuery
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from usefulfunc.builder import keyboard_builder


admin_rout = Router()


class AdminStates(StatesGroup):
    delete_students = State()
    delete_one_student = State()


@admin_rout.message(lambda mes: mes.from_user.id == "admin_id" and mes.text == "/update")
async def new_school_year(message: Message, state: FSMContext):
    with sq.connect("pupils.db") as con:
        cur = con.cursor()
        cur.execute(f"""UPDATE pupils SET grade = grade + 1
        WHERE grade NOT BETWEEN 9 AND 11
        """)
    kb = keyboard_builder(2, "Да", "Нет")
    await message.answer(text="Данные обновлены! Вы уверены, что хотите удалить некоторые записи?", reply_markup=kb)
    await state.set_state(AdminStates.delete_students)


@admin_rout.callback_query(StateFilter(AdminStates.delete_students), lambda cal: cal.from_user.id == "admin_id")
async def delete_students(callback: CallbackQuery, state: FSMContext):
    if callback.data == "Да":
        with sq.connect("pupils.db") as con:
            cur = con.cursor()
            cur.execute("PRAGMA foreign_keys = ON;")
            cur.execute(f"""DELETE FROM pupils
            WHERE grade BETWEEN 9 AND 11
            """)
        await callback.message.answer(text="Данные удалены")
    else:
        await callback.message.answer(text="Ок")
    await state.clear()


@admin_rout.message(lambda mes: mes.text == "/delete_one_student" and mes.from_user.id == "admin_id")
async def say_delete_student(message: Message, state: FSMContext):
    await message.answer(text="Введи имя и фамилию ученика, которго хотие удалить:")
    await state.set_state(AdminStates.delete_one_student)


@admin_rout.message(StateFilter(AdminStates.delete_one_student), lambda mes: mes.from_user.id == "admin_id")
async def delete_student(message: Message, state: FSMContext):
    name, surname = message.text.split()
    try:
        with sq.connect("pupils.db") as con:
            cur = con.cursor()
            cur.execute("PRAGMA foreign_keys = ON;")
            cur.execute(f"""DELETE FROM pupils
            WHERE name = '{name}' AND surname = '{surname}'
            """)
        await message.answer(text="Ученик удалён!")

    except:
        await message.answer(text="Что-то пошло не по плану(")
    await state.clear()
