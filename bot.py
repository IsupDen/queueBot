import os
from contextlib import suppress

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

import db

API_TOKEN = os.environ.get('API_KEY')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

lab = CallbackData('lab', 'subject', 'number')
shower = CallbackData('lab', 'subject')
recorder = CallbackData('record', 'subject', 'number')


class User(StatesGroup):
    waiting_for_name = State()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await User.waiting_for_name.set()
    await message.answer('Привет!\nЭто бот для организации очереди!\nВведи свои фамилию и имя')


@dp.message_handler(state=User.waiting_for_name)
async def enter_name(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(db.register(message.from_user.id, message.text))
    await message.answer('Используете следующие команды:\n'
                         '/ready -- чтобы встать в очередь\n'
                         '/pass  -- чтобы выйти из очереди\n'
                         '/show  -- чтобы посмотреть очередь')


@dp.message_handler(commands=['ready'])
async def ready(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='ОПД', callback_data='ОПД'),
        types.InlineKeyboardButton(text='Программирование', callback_data='Программирование')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    with suppress(MessageNotModified):
        await message.answer('Выберете предмет:', reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='ОПД'))
async def add_opd(call: types.CallbackQuery):
    buttons = [
        types.InlineKeyboardButton(text='3️⃣', callback_data=lab.new(call.data, 3)),
        types.InlineKeyboardButton(text='4️⃣', callback_data=lab.new(call.data, 4)),
        types.InlineKeyboardButton(text='5️⃣', callback_data=lab.new(call.data, 5)),
        types.InlineKeyboardButton(text='6️⃣', callback_data=lab.new(call.data, 6)),
        types.InlineKeyboardButton(text='7️⃣', callback_data=lab.new(call.data, 7))
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    keyboard.add(*buttons)
    with suppress(MessageNotModified):

        await call.message.edit_text('Выберете номер лабораторной:', reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='Программирование'))
async def add_prog(call: types.CallbackQuery):
    buttons = [
        types.InlineKeyboardButton(text='5️⃣', callback_data=lab.new(call.data, 5)),
        types.InlineKeyboardButton(text='6️⃣', callback_data=lab.new(call.data, 6)),
        types.InlineKeyboardButton(text='7️⃣', callback_data=lab.new(call.data, 7)),
        types.InlineKeyboardButton(text='8️⃣', callback_data=lab.new(call.data, 8))
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    keyboard.add(*buttons)
    with suppress(MessageNotModified):
        await call.message.edit_text('Выберете номер лабораторной:', reply_markup=keyboard)


@dp.callback_query_handler(lab.filter())
async def add(call: types.CallbackQuery, callback_data: dict):
    with suppress(MessageNotModified):
        await call.message.edit_text(db.add_lab(call.from_user.id, callback_data['subject'], callback_data['number']))


@dp.message_handler(commands=['show'])
async def show(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='ОПД', callback_data=shower.new('ОПД')),
        types.InlineKeyboardButton(text='Программирование', callback_data=shower.new('Программирование'))
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    with suppress(MessageNotModified):
        await message.answer('Выберете предмет:', reply_markup=keyboard)


@dp.callback_query_handler(shower.filter())
async def show_queue(call: types.CallbackQuery, callback_data: dict):
    with suppress(MessageNotModified):
        queue = db.show(callback_data['subject'])
        answer = ''
        for student in queue:
            answer += ': лабораторная №'.join([student[0], str(student[1])]) + '\n'
        await call.message.edit_text(callback_data['subject'] + '\n' + answer)


@dp.message_handler(commands=['pass'])
async def remove(message: types.Message):
    records = db.show_records(message.from_user.id)
    buttons = []
    for record in records:
        buttons.append(types.InlineKeyboardButton(text=' №'.join([record[0], str(record[1])]), callback_data=recorder.new(record[0], record[1])))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    with suppress(MessageNotModified):
        await message.answer('Выберете запись:', reply_markup=keyboard)


@dp.callback_query_handler(recorder.filter())
async def remove_record(call: types.CallbackQuery, callback_data: dict):
    with suppress(MessageNotModified):
        await call.message.edit_text(db.remove_lab(call.from_user.id, callback_data['subject'], callback_data['number']))


@dp.message_handler()
async def helper(message: types.Message):
    await message.answer('Используете следующие команды:\n'
                         '/ready -- чтобы встать в очередь\n'
                         '/pass  -- чтобы выйти из очереди\n'
                         '/show  -- чтобы посмотреть очередь')


if __name__ == '__main__':
    db.create_db()
    executor.start_polling(dp, skip_updates=True)

