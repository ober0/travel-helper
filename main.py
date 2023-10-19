'''
# 1)start
# 2)help
# 3)кнопки
# 4)свой ввод
# 5)бд для инфы
# 6)бд для баланса
# 7) команда для +денег
# 8) команда для показа последних 10 трат
# 9) команда для показа баланса
# 10) команда для показа кнопок
# 11)команда для удаления последней операции
# 12) /CheckLongHistoryOfSpending
13)ежедневное напомние
14)залить на хост
'''



import telebot
import sqlite3
from telebot import types
import re
import datetime
import csv


bot = telebot.TeleBot("6402207060:AAFIYlwlnxbLkN8MgXZSPUgnMbxp0zuf7FU")



def replenishment_process(message, count):
    try:
        db = sqlite3.connect("main.sql")
        cursor = db.cursor()
        cursor.execute(f"SELECT balance FROM UserBalance{message.chat.id} WHERE rowid = 1")
        money = int(cursor.fetchone()[0])
        money_new_value = money + count
        cursor.execute(f'UPDATE UserBalance{message.chat.id} SET balance = {money_new_value} WHERE rowid = 1')
        db.commit()
        db.close()

        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        btn1 = types.KeyboardButton("33р -> электричка")
        btn2 = types.KeyboardButton("16р -> электричка")
        btn3 = types.KeyboardButton("60р -> маршрутка")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, f'Успешно! Баланс: {money_new_value}', reply_markup=markup)

    except Exception as Ex:
        bot.send_message(message.chat.id, f"Произошла ошмбка СУБД: {Ex}")


def other_deposit(message):
    if message.text.lower() == 'cancel':
        bot.send_message(message.chat.id, 'Отменено!')
        return
    try:
        deposit = int(message.text)
        replenishment_process(message, deposit)
    except Exception as Ex:
        bot.send_message(message.chat.id, f'Значение должо быть числом!')
        bot.send_message(message.chat.id, f'Ошибка: {Ex}')
        return

def writing_off_money(id, cost):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT balance FROM UserBalance{id} where rowid = 1')
    new_bal = cursor.fetchone()[0]-cost
    cursor.execute(f'UPDATE UserBalance{id} SET balance = {new_bal} WHERE rowid = 1')
    db.commit()
    db.close()
def manual_input(message, time, cost):
    bot.send_message(message.chat.id, 'Введите тип траты:')
    bot.register_next_step_handler(message, manual_input_step2, time, cost)

def manual_input_step2(message, time_now, cost):
    characteristic = str(message.text)
    if type(cost) == int and type(characteristic) == str and type(time_now) == str:
        try:
            db = sqlite3.connect('main.sql')
            cursor = db.cursor()
            cursor.execute("INSERT INTO user{0} (type, cost, date) VALUES (?, ?, ?)".format(message.chat.id),
                           (characteristic, cost, time_now))
            db.commit()
            db.close()
            writing_off_money(message.chat.id, cost)

            db = sqlite3.connect('main.sql')
            cursor = db.cursor()
            cursor.execute(f'SELECT balance FROM UserBalance{message.chat.id} where rowid = 1')
            bal = cursor.fetchone()[0]
            db.close()
            bot.send_message(message.chat.id, f"Успешно. Остаток: {bal}")
        except Exception as Ex:
            bot.send_message(message.chat.id, f"Произошла  СУБД: {Ex}")


@bot.message_handler(commands=['CheckLongHistoryOfSpending'])
def create_table(message):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT * FROM user{message.chat.id} ORDER BY rowid DESC')
    all_data = cursor.fetchall()
    for i in range(len(all_data)):
        all_data[i] = list(all_data[i])
    with open(f'tables/user-{message.chat.id}-history.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';', lineterminator='\n')
        for row in all_data:
            csvwriter.writerow(row)
    bot.send_message(message.chat.id, 'Успешно! Таблица со всеми данными:')

    file = open(f'tables/user-{message.chat.id}-history.csv', 'r')
    bot.send_document(message.chat.id, file)

@bot.message_handler(commands=['remove_last'])
def remove_last(message):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    cursor.execute(f'DELETE FROM user{message.chat.id} WHERE rowid = (SELECT max(rowid) FROM user{message.chat.id})')
    db.commit()
    db.close()
    bot.send_message(message.chat.id, 'Успешно!')


@bot.message_handler(commands=['see_buttons'])
def see_buttons(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("33р -> электричка")
    btn2 = types.KeyboardButton("16р -> электричка")
    btn3 = types.KeyboardButton("60р -> маршрутка")
    markup.add(btn1, btn2, btn3)

    bot.send_message(message.chat.id, 'Выберите:', reply_markup=markup)

@bot.message_handler(commands=['balance'])
def see_balance(message):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT balance FROM UserBalance{message.chat.id} where rowid = 1')
    balance = cursor.fetchone()[0]
    db.close()
    bot.send_message(message.chat.id, f'Ваш баланс: {balance}руб.')


@bot.message_handler(commands=['last'])
def last_spending(message):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT * FROM user{message.chat.id} ORDER BY rowid DESC LIMIT 10')
    last10 = cursor.fetchall()

    num = 0
    last10_str = ''
    for i in last10:
        if type(i) == tuple:
            num += 1
            spend_name = i[0]
            spend_cost = i[1]
            spend_time = i[2]
            last10_str += f'{num}) {spend_name} - {spend_cost}руб ({spend_time})\n'
    bot.send_message(message.chat.id, f'<b>Ваши последние траты:</b>\n{last10_str}', parse_mode='html')
    bot.message_handler(message.chat.id, 'Для просмотра более большой истории - /CheckLongHistoryOfSpending')
@bot.message_handler(commands=["start"])
def start(message):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    try:
        cursor.execute(f'''CREATE TABLE UserBalance{message.chat.id} (balance int)''')
        db.commit()
        cursor.execute(f'INSERT INTO UserBalance{message.chat.id} VALUES (0)')
        db.commit()
    except:
        pass

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS user{message.chat.id} (
        type text,
        cost int,
        date text
    )''')
    db.commit()

    db.close()

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("33р -> электричка")
    btn2 = types.KeyboardButton("16р -> электричка")
    btn3 = types.KeyboardButton("60р -> маршрутка")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Привет! Я бот для помощи с твоим проездом! /help для помощи", reply_markup=markup)


@bot.message_handler(commands=["replenishment"])
def replenishment(message):
    markup1 = types.ReplyKeyboardMarkup()
    bot.send_message(message.chat.id, '<b> Пополнение </b>', parse_mode='html',
                     reply_markup=markup1)

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('1000р', callback_data='1000r_replenishment')
    btn2 = types.InlineKeyboardButton('2000р', callback_data='2000r_replenishment')
    btn3 = types.InlineKeyboardButton('3000р', callback_data='3000r_replenishment')
    btn4 = types.InlineKeyboardButton('4000р', callback_data='4000r_replenishment')
    btn5 = types.InlineKeyboardButton('5000р', callback_data='5000r_replenishment')
    btn6 = types.InlineKeyboardButton('Другое', callback_data='other')
    markup.row(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id, 'Воспользуйтесь нопкой ниже:',
                     reply_markup=markup)

@bot.message_handler(commands=['test'])
def test(message):
    db = sqlite3.connect('main.sql')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM user{message.chat.id}")
    print(cursor.fetchall())



@bot.message_handler(content_types=['text'])
def main(message):



    time_now = str(str(datetime.datetime.now()).split(".")[0])
    if len(message.text.split(' -> ')) == 2:
        try:
            cost = message.text.split(' -> ')[0]
            cost = int(re.sub(r'\D', '', cost))
            characteristic = str(message.text.split(' -> ')[1])
        except Exception as Ex:
            bot.send_message(message.chat.id, f"Произошла ошибка: {Ex}")

        if type(cost) == int and type(characteristic) == str and type(time_now) == str:
            try:

                db = sqlite3.connect('main.sql')
                cursor = db.cursor()
                cursor.execute("INSERT INTO user{0} (type, cost, date) VALUES (?, ?, ?)".format(message.chat.id), (characteristic, cost, time_now))
                db.commit()
                db.close()
                writing_off_money(message.chat.id, cost)

                db = sqlite3.connect('main.sql')
                cursor = db.cursor()
                cursor.execute(f'SELECT balance FROM UserBalance{message.chat.id} where rowid = 1')
                bal = cursor.fetchone()[0]
                db.close()
                bot.send_message(message.chat.id, f"Успешно. Остаток: {bal}")
            except Exception as Ex:
                bot.send_message(message.chat.id, f"Произошла  СУБД: {Ex}")
    else:
        try:
            cost = int(message.text)
            manual_input(message, time_now, cost) if cost > 0 else bot.send_message(message.chat.id, 'Трата не может быть отрицательной!')
        except:
            bot.send_message(message.chat.id, "Напишите только цифру, или воспользуйесь кнопками")




@bot.callback_query_handler(func=lambda callback: True)
def callback(callback):
    if callback.data != 'other':
        key_list = {
            "1000r_replenishment": 1000,
            "2000r_replenishment": 2000,
            "3000r_replenishment": 3000,
            "4000r_replenishment": 4000,
            "5000r_replenishment": 5000,
        }
        replenishment_process(callback.message, key_list[callback.data])
        return
    else:
        bot.send_message(callback.message.chat.id, 'Введите сумму пополнения (Отмена - cancel):')
        bot.register_next_step_handler(callback.message, other_deposit)


bot.polling(none_stop=True)