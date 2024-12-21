from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from crud_functions import initiate_db, get_all_products, add_user, is_included
API_TOKEN = ''
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
initiate_db()
def add_sample_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    sample_products = [
        ("Product1", "Описание 1", 100),
        ("Product2", "Описание 2", 200),
        ("Product3", "Описание 3", 300),
        ("Product4", "Описание 4", 400),]
    cursor.executemany('INSERT INTO Products (title, description, price) VALUES (?, ?, ?)', sample_products)
    conn.commit()
    conn.close()
#add_sample_products()  # Закомментировать
class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()
class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
@dp.message_handler(Command('start'))
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Рассчитать", "Информация", "Купить", "Регистрация"]
    keyboard.add(*buttons)
    await message.answer("Привет! Я бот, помогающий твоему здоровью.", reply_markup=keyboard)
@dp.message_handler(lambda message: message.text == 'Регистрация')
async def sing_up(message: types.Message):
    await RegistrationState.username.set()
    await message.answer("Введите имя пользователя (только латинский алфавит):")
@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.answer("Пользователь существует, введите другое имя.")
    else:
        await state.update_data(username=username)
        await RegistrationState.email.set()
        await message.answer("Введите свой email:")
@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await RegistrationState.age.set()
    await message.answer("Введите свой возраст:")
@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = message.text
    data = await state.get_data()
    username = data['username']
    email = data['email']
    add_user(username, email, age)
    await message.answer("Регистрация завершена!")
    await state.finish()
@dp.message_handler(lambda message: message.text == 'Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()  # Получаем все продукты из базы данных
    inline_keyboard = InlineKeyboardMarkup()

    for product in products:
        title, description, price = product
        inline_keyboard.add(
            InlineKeyboardButton(title, callback_data=title))  # Используем название продукта как callback_data
        await message.answer(f'Название: {title} | Описание: {description} | Цена: {price}')
        # Здесь предполагается, что изображения хранятся в определенной директории
        image_path = f'C:\\Users\\Михалыч\\PycharmProjects\\pythonProject5\\{title}.jpg'
        await message.answer_photo(photo=open(image_path, 'rb'))

    await message.answer("Выберите продукт для покупки:", reply_markup=inline_keyboard)
@dp.callback_query_handler(lambda call: True)
async def process_callback(call: types.CallbackQuery):
    product_title = call.data
    await call.answer(f"Вы выбрали продукт: {product_title}")
@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.add(
        InlineKeyboardButton("Рассчитать норму калорий", callback_data='calories'),
        InlineKeyboardButton("Формулы расчёта", callback_data='formulas')
    )
    await message.answer("Выберите опцию:", reply_markup=inline_keyboard)
@dp.callback_query_handler(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    formula_message = (
        "Формула Миффлина-Сан Жеора:\n"
        "Для мужчин: BMR = 10 * вес(кг) + 6.25 * рост(см) - 5 * возраст(лет) + 5\n"
        "Для женщин: BMR = 10 * вес(кг) + 6.25 * рост(см) - 5 * возраст(лет) - 161"
    )
    await call.message.answer(formula_message)
    await call.answer()
@dp.callback_query_handler(lambda call: call.data == 'calories')
async def set_age(call: types.CallbackQuery):
    await UserState.age.set()
    await call.message.answer("Введите свой возраст:")
    await call.answer()
@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await UserState.growth.set()
    await message.answer("Введите свой рост:")
@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await UserState.weight.set()
    await message.answer("Введите свой вес:")
@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    data = await state.get_data()
    age = int(data['age'])
    growth = int(data['growth'])
    weight = int(data['weight'])
    calories = 10 * weight + 6.25 * growth - 5 * age + 5
    await message.answer(f"Ваша норма калорий: {calories:.2f} ккал.")
    await state.finish()
@dp.callback_query_handler(lambda call: call.data == 'product_buying')
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()
@dp.errors_handler()
async def error_handler(update, exception):
    print(f'Произошла ошибка: {exception}')
    return True
@dp.message_handler()
async def all_messages(message: types.Message):
    await message.answer('Введите команду /start, чтобы начать общение.')
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
