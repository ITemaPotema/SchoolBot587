from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, PollAnswer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from usefulfunc.create_hash import create_hash, PASSWORD
from usefulfunc.db_commands import insert_db, select

start_rout = Router()
bot: Bot = Bot(token='6457157815:AAEax-ECU_DegEbtj7p8LjOrXUdtjAFvrdw')


class ProjectStates(StatesGroup):
    password = State()
    name = State()
    surname = State()
    photo = State()
    grade = State()
    interests = State()
    info = State()


translate = {"name": "Введите фамилию:",
             "surname": "Отправьте аватарку профиля:",
             "photo": "В каком классе вы учитесь(пример: 7А):",
             "grade": "Укажите ваши интересы(выберите ТРИ наиболее важные для Вас)",
             "interests": "Укажите информацию о себе, увлечения и т.д.",
             "info": "Поздравляю!!! Профиль успешно создан",
            }


@start_rout.message(Command(commands=["start"]))
async def start_func(message: Message, state: FSMContext):
    cond = f"WHERE tg_name = {message.from_user.id}"
    data = bool(select("pupils.db", "pupils", ["*"], condition=cond))
    if not data:
        text = """Привет, этот бот создан для общения и знакомств учеников 587 Гимназии.
Чтобы получить доступ к функциям бота,получите и введите пароль, опубликованный в тг прослушки, а также создайте профиль.
Приятного время препровождения, скуфяры)))"""
        await message.answer(text=text)
        if message.from_user.id == 5103563816:
            await message.answer(text="Команды админа: /update(обновляет классы),"
                                      " /delete_one_student")
        await message.answer(text="Введи пароль:")
        await state.set_state(ProjectStates.password)
    else:
        await message.answer(text="Вы уже зарегистрированы!!!")


@start_rout.message(StateFilter(ProjectStates.password), F.text.isdigit())
async def get_password(message: Message, state: FSMContext):
    text = message.text
    if create_hash(text) == PASSWORD:
        welcome_text = "Успешно, теперь перейдём к оформлению профиля"
        await message.answer(text=welcome_text)
        await message.answer(text="Введи имя:")
        await state.set_state(ProjectStates.name)

    else:
        await message.answer("Неверный пароль")


@start_rout.message(StateFilter(ProjectStates.name))
async def get_name(message: Message, state: FSMContext):
    name = message.text
    if name.isalpha() and 2 < len(name) <= 20:
        await message.answer(text=translate["name"])
        await state.set_state(ProjectStates.surname)
        await state.update_data(name=name)
    else:
        await message.answer(text="Ошибка ввода!")


@start_rout.message(StateFilter(ProjectStates.surname))
async def get_surname(message: Message, state: FSMContext):
    surname = message.text
    if surname.isalpha() and 2 < len(surname) <= 20:
        await message.answer(text=translate["surname"])
        await state.set_state(ProjectStates.photo)
        await state.update_data(surname=surname)
    else:
        await message.answer(text="Ошибка ввода!")


@start_rout.message(StateFilter(ProjectStates.photo))
async def get_photo(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        await message.answer(text=translate["photo"])
        await state.set_state(ProjectStates.grade)
        await state.update_data(photo=file_id)
    else:
        await message.answer("Пришли мне ФОТО!!!")


@start_rout.message(StateFilter(ProjectStates.grade))
async def get_grade(message: Message, state: FSMContext):
    username = message.from_user.id
    if message.text:
        grade1 = message.text.upper()
        if 6 <= int(grade1[:len(grade1)-1]) <= 11 and grade1[-1] in ("А", "Б", "В", "Г", "Д"):
            await message.answer(text=translate["grade"])
            grade = grade1[:len(grade1)-1]
            letter = grade1[len(grade1)-1]
            await state.update_data(grade=grade, letter=letter)
            await state.set_state(ProjectStates.interests)
            options = ["Спорт", "IT", "Кино/аниме", "Музыка", "Компьютерные игры", "Рисование", "Книги", "Научпоп",
                   "Иностранные языки", "Психология"]
            await bot.send_poll(chat_id=username, question="Интересы", options=options, allows_multiple_answers=True, is_anonymous=False)
        else:
            await message.answer(text="Ошибка ввода!")
    else:
        await message.answer(text="Ошибка ввода!")


@start_rout.poll_answer(StateFilter(ProjectStates.interests))
async def get_interests(poll: PollAnswer, state: FSMContext):
    user_id = poll.user.id
    answers = "".join(list(map(lambda x: str(x + 1), poll.option_ids)))
    if len(answers) == 3:
        await bot.send_message(chat_id=user_id, text=f"{translate['interests']}")
        await state.set_state(ProjectStates.info)
        await state.update_data(interests=answers)
    else:
        await bot.send_message(chat_id=user_id, text="Я просил выбрать ТРИ интереса!")
        options = ["Спорт", "IT", "Кино/аниме", "Музыка", "Компьютерные игры", "Рисование", "Книги", "Научпоп",
                    "Иностранные языки", "Психология"]
        await bot.send_poll(chat_id=user_id, question="Интересы", options=options,
                            allows_multiple_answers=True, is_anonymous=False)


@start_rout.message(StateFilter(ProjectStates.info))
async def get_info(message: Message, state: FSMContext):
    info = message.text
    username = message.from_user.id
    if len(message.text) > 10:
        await message.answer(text=translate["info"])
        await state.update_data(info=info)
        data = await state.get_data()
        data = dict(data)
        values = (username,) + tuple(data.values())
        insert_db("pupils.db", "pupils", values)
        await state.clear()
    else:
        await message.answer("Слишком мало!!! Расскажите больше!!!")


