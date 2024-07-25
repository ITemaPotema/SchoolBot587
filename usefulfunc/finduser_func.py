from usefulfunc.builder import keyboard_builder
from usefulfunc.db_commands import select


async def default_states(message, state, cl):
    if select("pupils.db", "pupils", "*", f"WHERE tg_name = '{message.from_user.id}'"):
        btn_names = [str(i) for i in range(6, 12)]
        keyboard = keyboard_builder(6, *btn_names)
        await message.answer(text="Выбери параллель:", reply_markup=keyboard)
        await state.set_state(cl.letter)
    else:
        await message.answer(text="Ошибка! Скорее всего Вы были заблокированы!")


async def back_to_pattern(callback, state, cl):
    if callback.data != "Выйти":
        btn_names = [str(i) for i in range(6, 12)]
        keyboard = keyboard_builder(6, *btn_names)
        await callback.message.answer(text="И снова выбери параллель:", reply_markup=keyboard)
        await default_states(callback, state, cl)
    else:
        await callback.message.answer(text='Жду новых команд!')
        await state.clear()

