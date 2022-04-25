import os
from contextlib import suppress

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ParseMode, InputTextMessageContent, InlineQueryResultArticle
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

import db
import logging

logging.basicConfig(level=logging.INFO,
                    filename='logs',
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt='%d/%m/%y %H:%M:%S')

API_TOKEN = os.environ.get('API_KEY')
ADMIN_ID = os.environ.get('ADMIN_ID')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

lab = CallbackData('lab', 'subject', 'number')
shower = CallbackData('lab', 'subject')
recorder = CallbackData('record', 'subject', 'number')
admin_add = CallbackData('add', 'student', 'subject', 'number')
admin_drop = CallbackData('drop', 'student', 'subject', 'number')


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
    logging.info('Новый пользователь: ' + message.text)
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
        if db.add_lab(call.from_user.id, callback_data['subject'], callback_data['number']):
            await call.message.edit_text('Вы успешно добавлены в очередь!')
            logging.info(
                db.get_name(call.from_user.id)[0] + ' встал в очередь на лабораторную ' + callback_data['subject'] +
                callback_data['number'])
        else:
            await call.message.edit_text('Вы уже находитесь в очереди на эту лабораторную работу!')
            logging.info(db.get_name(call.from_user.id)[0] + ' попытался повторно встать в очередь на лабораторную ' +
                         callback_data['subject'] + callback_data['number'])


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
        answer = '<code>'
        i = 1
        for student in queue:
            answer += ('%2d' % i) + ")"
            i += 1
            answer += '%-25s' % student[0] + str(student[1]) + '\n'
        await call.message.edit_text(callback_data['subject'] + '\n' + answer + '</code>', parse_mode=ParseMode.HTML)
        logging.info(db.get_name(call.from_user.id)[0] + ' посмотрел очередь')


@dp.message_handler(commands=['pass'])
async def remove(message: types.Message):
    records = db.show_records(message.from_user.id)
    buttons = []
    for record in records:
        buttons.append(types.InlineKeyboardButton(text=' №'.join([record[0], str(record[1])]),
                                                  callback_data=recorder.new(record[0], record[1])))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    with suppress(MessageNotModified):
        await message.answer('Выберете запись:', reply_markup=keyboard)


@dp.callback_query_handler(recorder.filter())
async def remove_record(call: types.CallbackQuery, callback_data: dict):
    with suppress(MessageNotModified):
        await call.message.edit_text(
            db.remove_lab(call.from_user.id, callback_data['subject'], callback_data['number']))
        logging.info(
            db.get_name(call.from_user.id)[0] + ' сдал лабораторную ' + callback_data['subject'] + callback_data[
                'number'])


@dp.message_handler(commands=['journal'])
async def show(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='ОПД',
                                   url='https://docs.google.com/spreadsheets/d/1Y_qW9PYSSuiEkKr56tw4Q4ZYcASunhfVL6X82dWvULo/edit#gid=1957069157'),
        types.InlineKeyboardButton(text='Программирование',
                                   url='https://docs.google.com/spreadsheets/d/1cEvt5QcRtsLlS_taVT24gelxKZ3DYMgv1cnMwA3ta90/edit#gid=302060594')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    await message.answer('Выберете предмет:', reply_markup=keyboard)


@dp.message_handler()
async def helper(message: types.Message):
    await message.answer('Используете следующие команды:\n'
                         '/ready   -- чтобы встать в очередь\n'
                         '/pass    -- чтобы выйти из очереди\n'
                         '/show    -- чтобы посмотреть очередь\n'
                         '/journal -- чтобы перейти к журналу')


@dp.inline_handler()
async def inline_handler(query: types.InlineQuery):
    items = []
    subjects = ['ОПД', 'Программирование']
    for subject in subjects:
        queue = db.show(subject)
        answer = '<code>'
        i = 1
        for student in queue:
            answer += ('%2d' % i) + ")"
            i += 1
            answer += '%-25s' % student[0] + str(student[1]) + '\n'
        answer = subject + ':\n' + answer + '</code>'
        input_content = InputTextMessageContent(answer, parse_mode=ParseMode.HTML)
        items.append(InlineQueryResultArticle(
            id=subject,
            title=subject,
            input_message_content=input_content, )
        )
        print(answer)
    await query.answer(items, cache_time=30)


if __name__ == '__main__':
    db.connect()
    db.create_db()
    executor.start_polling(dp, skip_updates=True)
