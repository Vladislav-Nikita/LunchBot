import telebot
from telebot import types
from datetime import datetime
from pg_bot_funcs import *
from time import sleep
from ast import literal_eval
# from termcolor import colored
# import telegram
# import schedule
# import psycopg2 as pg
import time

# import logging
# from pg_bot_funcs import users_table_name, orders_table_name

try:
    with open('yummyBot.ini', 'r', encoding='utf-8') as ini_file:
        lines = ini_file.readlines()
        for line in lines:
            if line.startswith('token'):
                TOKEN = line.split('=')[-1].strip('\n')
            elif line.startswith('db_name'):
                db_name = line.split('=')[-1].strip('\n')
            elif line.startswith('host'):
                db_host = line.split('=')[-1].strip('\n')
            elif line.startswith('port'):
                db_port = line.split('=')[-1].strip('\n')
            elif line.startswith('db_pass'):
                db_pass = line.split('=')[-1].strip('\n')
            elif line.startswith('db_username'):
                db_username = line.split('=')[-1].strip('\n')
            elif line.startswith('users_table_name'):
                users_table_name = line.split('=')[-1].strip('\n')
            elif line.startswith('orders_table_name'):
                orders_table_name = line.split('=')[-1].strip('\n')
            elif line.startswith('company'):
                company = line.split('=')[-1].strip('\n')
            elif line.startswith('UCN'):
                UCN = line.split('=')[-1].strip('\n')
        ini_file.close()
except Exception as e:
    bot.send_message(admins[0], f"ini_file doesn't works\n{e}")

db_host = 'localhost'
db_port = '5432'
send_time = '23:00'


# company_name = 'Yummy Cafe'
# app_name = 'telegram'


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, ex):
        global admins

        print(ex)
        bot.send_message(admins[0], ex)
        return True


# 6425771542:AAHO12E22_BEz-srB25i99_L9al-ABCUH_w -- Cafe Bot
# 6559204532:AAF2nawhBA3Mze0rm9hDIOgJ4-kpNJ9xVXQ -- LunchBot

bot = telebot.TeleBot(TOKEN,
                      exception_handler=ExceptionHandler())

# поменять команды для разных ролей
# https://stackoverflow.com/questions/74959699/telebot-how-to-create-a-list-of-commands-manually-and-unique-for-different-user
bot.set_my_commands(
    commands=[
        telebot.types.BotCommand('/start', 'Старт'),
        telebot.types.BotCommand('/stop', 'Выход (удаление из базы)'),
        telebot.types.BotCommand('/role', 'Роли'),
        telebot.types.BotCommand('/update', 'Обновление меню'),
        telebot.types.BotCommand('get_orders', 'Файл с заказами')
    ]
)

# us_tab_nam = users_table_name
# Получаем из бд
valid_users = []
user_nicknames = {}
admins = []
cooks = []
admin_pass = 'oaq873ergf'
cook_pass = 'zRgcu*T{zB'
companies = {}
cnx = get_connection()
orders_params = get_table_columns(cnx, orders_table_name)
cnx.close()
ord_par_str = '('
for el in orders_params:
    ord_par_str += el
    ord_par_str += ', '
ord_par_str = ord_par_str[:-2]
ord_par_str += ')'


# print(companies)

def update_users():
    global valid_users, cooks, admins, user_nicknames, users_table_name

    cnx = get_connection()
    valid_users = get_all_users_id_as_list(cnx, users_table_name)
    cooks = get_all_users_id_as_list(cnx, users_table_name, 'cook')
    # cooks.append(589562037)
    admins = get_all_users_id_as_list(cnx, users_table_name, 'admin')
    user_nicknames = get_all_users_nicknames_as_dict(cnx)
    cnx.close()


update_users()

# Хранятся заказы в виде:
# {user_id1: {dish1: num1, ...}, user_id2: {dish4: num3, ...}, ...}
all_orders = {}
# {user_id: order_id,...}
ids_orders = {}

# Хранятся суммы заказов
# {user_id1: total1, user_id2: total2,...}
totals = {}

# Хрянятся тайминги, когда пользователь заказал
# {user_id1: (date, time), ...}
order_timings = {}

# Меню в виде
# {category1: {dish1: price1, dish2: price2, ...}, ...}
menu = {}
menu_date = ''
menu_date_obj = datetime.today()

# Все блюда подряд: {dish1: price1, dish2: price2, ...}
dish_prices = {}

# Состав и граммовки блюд
# {dish1: [состав, граммовка]}
dish_info = {}

weekdays_list = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница',
                 'суббота', 'воскресенье']


def day_of_week(date_str):
    global weekdays_list
    return weekdays_list[datetime.strptime(date_str, "%d.%m.%Y").weekday()]


def rassilka(users_list: list, msg: str):
    for user in users_list:
        bot.send_message(user, msg)


def init_menu():
    global menu, dish_prices, menu_date, menu_date_obj, dish_info, all_orders, \
        totals, order_timings

    try:
        menu, dish_prices, menu_date, menu_date_obj, dish_info = {}, {}, '', None, {}

        all_orders, totals, order_timings = {}, {}, {}

        with open('menu.txt', 'r', encoding='utf-8') as menu_file:
            lines = menu_file.readlines()
            menu_date = f'{day_of_week(lines[0][:-1])} {lines[0][:-1]} '
            menu_date_obj = datetime.strptime(lines[0][:-1], "%d.%m.%Y")
            category = ''
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    category = line[1:-1]
                    if category == 'Первые блюда':
                        category = '🍲 ' + category
                    elif category == 'Вторые блюда':
                        category = '🍗 ' + category
                    elif category == 'Гарниры':
                        category = '🍝 ' + category
                    elif category == 'Салаты':
                        category = '🥗 ' + category
                    elif category == 'Zoom завтраки':
                        category = '🥞 ' + category

                    menu.update({category: {}})
                    # menu[category] = {}
                elif line.startswith('Описание;'):
                    dish_info.update({dish_name: line[line.index(';') + 1:]})
                    # dish_info[dish_name].append(line[line.index(';') + 1:])
                else:
                    dish_name, dish_price = line.split(';')
                    menu[category].update({dish_name: float(dish_price)})
        menu_file.close()
        for i in list(menu.values()):
            dish_prices.update(i)
        # rassilka(valid_users, 'Готов принять ваш заказ')
    except Exception as e:
        bot.send_message(admins[0], f"init_menu doesn't works\n{e}")


init_menu()


# Создание интерфейса
def create_buttons(categ=None, user_id=None, lvl=None):
    back_btn = types.KeyboardButton('◀ Назад️')
    confirm_btn = types.KeyboardButton(text='✅ Оформить заказ')
    remove_btn = types.KeyboardButton(text='✏ Редактирование')
    clear_btn = types.KeyboardButton(text='🗑 Очистить заказ')
    if lvl == 0:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton(text='Обновить меню'))
        markup.add(types.KeyboardButton(text='Обновить меню'))
        return markup
    elif categ is None and user_id is None:  # Создание главного меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        # markup.add(types.KeyboardButton(text='Обновить меню'))
        btn_arr = []
        for m in menu:
            btn_arr.append(types.KeyboardButton(text=f'{m}'))
        markup.add(*btn_arr)
        markup.row(confirm_btn, remove_btn, clear_btn)
        return markup
    elif categ is not None and user_id is None:  # Создание меню второго уровня
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for dish, price in menu[categ].items():
            markup.add(types.KeyboardButton(text=f'{dish}: {price}'))
        markup.row(confirm_btn, back_btn)
        return markup
    elif categ is None and user_id is not None:  # Создание меню в режиме удаления
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn_arr = []
        for dish, num in all_orders[user_id].items():
            btn_arr.append(types.KeyboardButton(text=f'{dish}    x{num}'))
        markup.add(*btn_arr)
        markup.row(confirm_btn, back_btn)
        return markup


# Создает сообщение с текущим заказом
def create_order_msg(message):
    global all_orders, totals, dish_prices

    msg = 'Ваш заказ:\n'
    total_price = 0
    for dish, num in all_orders[message.chat.id].items():
        price = dish_prices[dish]
        msg += f'{dish} -- {price} BYN.  x{num}\n'
        total_price += price * num
        total_price = round(total_price, 2)
    msg += f'\nИтого: {total_price} BYN.'
    totals.update({message.chat.id: total_price})
    return msg


# читаем значения подтвержденных заказов
def get_orders_vars_from_sys():
    try:
        f = open('sys_orders.txt', 'r', encoding='utf-8')
        lines = f.readlines()
        sys_orders, sys_order_timings, sys_totals, sys_dish_prices = {}, {}, {}, {}
        for line in lines:
            if line.startswith('All orders'):
                sys_orders = literal_eval(line[line.index(':') + 1:].strip())
            elif line.startswith('Order timings'):
                sys_order_timings = literal_eval(line[line.index(':') + 1:].strip())
            elif line.startswith('Totals'):
                sys_totals = literal_eval(line[line.index(':') + 1:].strip())
            elif line.startswith('Dish prices'):
                sys_dish_prices = literal_eval(line[line.index(':') + 1:].strip())
        f.close()
        return {'All orders': sys_orders, 'Order timings': sys_order_timings,
                'Totals': sys_totals, 'Dish prices': sys_dish_prices}
    except Exception as e:
        bot.send_message(admins[0], f'get_orders_vars_from_sys bad\n{e}')


# Записывает заказы в файл
def create_orders_file(message=None):
    global menu_date, user_nicknames

    try:
        sys_orders, sys_order_timings, sys_totals, sys_dish_prices = \
            get_orders_vars_from_sys().values()

        # ормируем файл нужного формата
        if message is None:
            f = open('orders.txt', 'w', encoding='utf-8')
            f.write(f'Заказы на {menu_date}:\n\n')
            # for user in sys_orders:
            #     (order_date, order_time) = sys_order_timings[user]
            #     f.write(f'Заказ {order_date} {order_time}; {user}\n')
            #     f.write(f'{user_nicknames[user]}\n')
            #     for dish, num in sys_orders[user].items():
            #         f.write(f'{dish}: {num} * {sys_dish_prices[dish]} = {num * sys_dish_prices[dish]}\n')
            #     f.write(f'\n'
            #             f'Итого: {sys_totals[user]}')
            #     f.write('\n_______________\n\n')
        else:
            (order_date, order_time) = sys_order_timings[message.chat.id]
            f = open('orders.txt', 'a', encoding='utf-8')
            f.write(f'Заказ {order_date} {order_time}; {message.chat.id}\n')
            f.write(f'{user_nicknames[message.chat.id]}\n')
            for dish, num in sys_orders[message.chat.id].items():
                f.write(f'{dish}: {num} * {sys_dish_prices[dish]} = {round(num * sys_dish_prices[dish], 2)}\n')
            f.write(f'\n'
                    f'Итого: {sys_totals[message.chat.id]}')
            f.write('\n_______________\n\n')

        f.close()
    except Exception as e:
        bot.send_message(admins[0], "create_orders_file doesn't works\n" + str(e))


# Записываем подтвержденные заказы в sys_orders.txt
def create_sys_orders_file():
    global all_orders, order_timings, totals, dish_prices

    try:
        f = open('sys_orders.txt', 'w', encoding='utf-8')
        f.write(f'All orders: {all_orders}\n')
        f.write(f'Order timings: {order_timings}\n')
        f.write(f'Totals: {totals}\n')
        f.write(f'Dish prices: {dish_prices}')
        f.close()
    except Exception as e:
        bot.send_message(admins[0], "create_sys_orders_file doesn't works\n" + str(e))


create_sys_orders_file()
create_orders_file()


# Функция кнопки "Показать меню"
def create_message_menu():
    global menu, dish_info, dish_prices, menu_date

    try:
        msg = f'Меню на {menu_date}:'
        msg += '\n'
        for categ in menu:
            msg += f'\n*{categ}*\n'
            for dish, price in menu[categ].items():
                msg += f'{dish} -- {price}\n'
                if dish in dish_info:
                    msg += f'{dish_info[dish]}\n'
        return msg
    except Exception as e:
        bot.send_message(admins[0], f'create_message_menu bad\n{e}')
        return str(menu)


# Создает сообщение для неавторизованного пользователя
def unknown_user(us_id):
    global bot
    bot.send_message(us_id, 'Не зарегистрированный пользователь')
    msg = 'Хотите зарегистрироваться?\nНажмите "Регистрация", для отправки Вашего' \
          ' Telegram ID администратору'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='Регистрация'))
    markup.add(types.KeyboardButton(text='Отмена'))
    bot.send_message(us_id, msg, reply_markup=markup)


# Функция для отправки админу уведомления о новом пользователе
def authorization_request(message, role='пользователь', recipient=admins):
    msg = f'Новый {role} хочет авторизоваться\n' \
          f'Name: {message.from_user.first_name} {message.from_user.last_name}\n' \
          f'Username: {message.from_user.username}\n' \
          f'id: {message.chat.id}'
    if isinstance(recipient, list):
        for rec in recipient:
            bot.send_message(rec, msg)
    else:
        bot.send_message(recipient, msg)
    if role == 'пользователь':
        role = 'null'
    elif role == 'админ':
        role = "'admin'"
    elif role == 'повар':
        role = "'cook'"
    sql_req = f"insert into {users_table_name}\n" \
              f"(user_tgid, first_name, last_name, username, special_role)\n" \
              f"values\n" \
              f"({message.chat.id},'{message.from_user.first_name}','{message.from_user.last_name}'," \
              f"'{message.from_user.username}',{role});"
    if isinstance(recipient, list):
        for rec in recipient:
            bot.send_message(rec, sql_req)
    else:
        bot.send_message(recipient, sql_req)
    msg = f'Запрос на регистрацию успешно отправлен!'
    bot.send_message(message.chat.id, msg)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='◀ Назад'))
    markup.add(types.KeyboardButton(text='Готово'))
    bot.send_message(message.chat.id, 'Нажмите любую кнопку', reply_markup=markup)


def is_good_time(st=send_time):
    global menu_date_obj

    send_time_obj = datetime.strptime(st, "%H:%M").time()
    delta = menu_date_obj.date() - datetime.now().date()
    if delta.days > 1 or (datetime.now().time() < send_time_obj and delta.days == 1):
        return True
    else:
        return False


def write_order_in_db(message):
    try:
        global all_orders, order_timings, totals, dish_prices
        cnx = get_connection()
        params = '(ceunikey, cedoccod, ceobnam, neopexp, neoppric, neopsumc)'
        # уникальный ключ заказа,тип строки, наименование товара, кол-во, цена, сумма
        order = all_orders[message.chat.id]
        ceuniref0 = UCN
        ceuniref2 = 'null'
        tedocpay = '01.01.0001 00:00:00'
        (dat, tim) = order_timings[message.chat.id]
        dat = dat.replace('.', '')
        ceuniref1 = f'Order {message.chat.id} {dat}{tim.replace(":", "")}'
        tedocins = f'{dat}{tim.replace(":", "")}'

        # Для записи наименований
        for dish, num in order.items():
            # ceunikey = datetime.now().strftime('%y%m%d%H%M%S%f')[:-3] + '0' + ceuniref0 + companies[app_name]
            ceunikey = datetime.now().strftime('%y%m%d%H%M%S%f')[:-3] + '0' + ceuniref0 + str(message.chat.id)
            sleep(0.001)
            ceunifol = f'{datetime.now().strftime("%Y%m%d %H:%M:%S")} {message.chat.id}'
            cedoccod = 'Order'
            tedocact = 'null'
            ceobide = 'null'
            ceobnam = dish
            ceobtyp = 'ТОВАР'
            ceobmea = 'null'
            neopexp = num
            neoppric = dish_prices[dish]
            neopsumc = round(dish_prices[dish] * num, 2)
            neopdelc = 0  # Скидка от 0 до 1
            neoptotc = round((1 - neopdelc) * neopsumc, 2)
            value = f"""('{ceunikey}', '{ceuniref0}', '{ceuniref1}', {ceuniref2}, '{ceunifol}', 
            '{cedoccod}', {tedocact}, '{tedocins}', '{tedocpay}', {ceobide}, '{ceobnam}', '{ceobtyp}',
             {ceobmea}, {neopexp}, {neoppric}, {neopsumc}, {neopdelc}, {neoptotc});"""
            insert(cnx, orders_table_name, ord_par_str, value)

        #  Для записи Total
        # ceunikey = datetime.now().strftime('%y%m%d%H%M%S%f')[:-3] + '0' + ceuniref0 + companies[app_name]
        ceunikey = datetime.now().strftime('%y%m%d%H%M%S%f')[:-3] + '0' + ceuniref0 + str(message.chat.id)
        ceunifol = f'{dat} {tim} {message.chat.id}'
        cedoccod = 'Total'
        tedocact = 'null'
        ceobide = 'null'
        ceobnam = 'null'
        ceobtyp = 'null'
        ceobmea = 'null'
        neopexp = 'null'
        neoppric = 'null'
        neopsumc = totals[message.chat.id]
        neopdelc = 0  # Скидка от 0 до 1
        neoptotc = round((1 - neopdelc) * neopsumc, 2)
        value = f"""('{ceunikey}', '{ceuniref0}', '{ceuniref1}', {ceuniref2}, '{ceunifol}', 
                    '{cedoccod}', {tedocact}, '{tedocins}', '{tedocpay}', {ceobide}, {ceobnam}, {ceobtyp},
                     {ceobmea}, {neopexp}, {neoppric}, {neopsumc}, {neopdelc}, {neoptotc});"""
        insert(cnx, orders_table_name, ord_par_str, value)
        cnx.close()
    except Exception as e:
        bot.send_message(admins[0], f'write_in_db doesnt works: \n{e}')


def on_delete_order(us_id):
    global totals, all_orders, order_timings
    try:
        del all_orders[us_id]
        del totals[us_id]
        try:
            del order_timings[us_id]
        except:
            pass
        create_sys_orders_file()
        # create_orders_file()
        # bot.send_message(us_id, 'Заказ пуст', reply_markup=create_buttons())
    except Exception as e:
        print(e)


@bot.message_handler(commands=['start'])
def start(message):
    global valid_users

    if message.chat.id in valid_users:
        bot.send_message(message.chat.id, f'Здравствуйте, '
                                          f'{message.from_user.first_name}! '
                                          f'Вы можете оформить заказ или отредактировать существующий.',
                         reply_markup=create_buttons())
    else:
        unknown_user(message.chat.id)


# Обработка команды /stop
@bot.message_handler(commands=['stop'])
def stop(message):
    global users_table_name  # Пришлось заменить, тк выдавало ошибку при users_table_name
    cnx = get_connection()
    delete(cnx, users_table_name, f'user_tgid={message.chat.id}')
    bot.send_message(message.chat.id, 'Вы были удалены из базы данных')
    cnx.close()


# Обработка команды /role
@bot.message_handler(commands=['role'])
def send_users_role(message):
    if message.chat.id in admins:
        bot.send_message(message.chat.id, 'Администратор')
    elif message.chat.id in cooks:
        bot.send_message(message.chat.id, 'Повар')
    elif message.chat.id in valid_users:
        bot.send_message(message.chat.id, "Авторизованный пользователь")
    else:
        bot.send_message(message.chat.id, "Неавторизованный пользователь")


# Обработка команды /update
# Функция, которая будет отправлять сообщение об обновлении меню
# def send_message():
#    message = '/update'
#    bot.send_message(chat_id=admins, text=message)

# Задаем время отправки сообщения
# schedule.every().day.at("14:24").do(send_message)


@bot.message_handler(commands=['update'])
def send_update(message):
    if message.chat.id in admins:
        bot.send_message(message.chat.id, f'Меню на {menu_date} успешно обновлено!')
        bot.send_message(message.chat.id, create_message_menu(),
                         parse_mode='Markdown')
    elif message.chat.id in valid_users:
        bot.send_message(message.chat.id, f'Меню на {menu_date} успешно обновлено!')
        bot.send_message(message.chat.id, create_message_menu(),
                         parse_mode='Markdown')


# Обработка поступающих сообщений
@bot.message_handler(content_types=['text'])
def bot_message(message):
    global menu, all_orders, totals, dish_prices, valid_users, admins, \
        cooks, menu_date, order_timings, send_time

    try:
        update_users()
        if message.chat.id in valid_users and message.chat.id not in cooks:  # Пользователь авторизован и роль не повар

            if message.text in menu:
                bot.send_message(message.chat.id, message.text,
                                 reply_markup=create_buttons(
                                     categ=message.text))

            elif message.text == '◀ Назад️' or message.text == 'Готово':
                bot.send_message(message.chat.id, message.text,
                                 reply_markup=create_buttons())

            elif message.text.split(':')[0].strip() in dish_prices:
                dish = message.text.split(':')[0].strip()
                if message.chat.id in all_orders:
                    if dish in all_orders[message.chat.id]:
                        all_orders[message.chat.id][dish] += 1
                    else:
                        all_orders[message.chat.id].update({dish: 1})
                else:
                    all_orders.update({message.chat.id: {dish: 1}})
                bot.send_message(message.chat.id, f'{dish} добавлен')
                bot.send_message(message.chat.id, create_order_msg(message))

            elif message.text.split('x')[0].strip() in dish_prices:
                dish = message.text.split('x')[0].strip()
                all_orders[message.chat.id][dish] -= 1

                if all_orders[message.chat.id][dish] == 0:
                    del all_orders[message.chat.id][dish]

                if all_orders[message.chat.id] == {}:
                    on_delete_order(message.chat.id)
                    bot.send_message(message.chat.id, 'Заказ пуст', reply_markup=create_buttons())
                else:
                    bot.send_message(message.chat.id, f'1 {dish} удален',
                                     reply_markup=create_buttons(
                                         user_id=message.chat.id))
                    bot.send_message(message.chat.id,
                                     create_order_msg(message))

            elif message.text == '🗑 Очистить заказ':
                # on_delete_order func
                if message.chat.id in all_orders:
                    on_delete_order(message.chat.id)
                    bot.send_message(message.chat.id, 'Заказ пуст', reply_markup=create_buttons())
            elif message.text == '✏ Редактирование':
                if message.chat.id in all_orders:
                    bot.send_message(message.chat.id, 'Вы можете отредактировать заказ',
                                     reply_markup=create_buttons(
                                         user_id=message.chat.id))

            elif message.text == '✅ Оформить заказ':
                if message.chat.id in all_orders:
                    order_time = datetime.today().time().isoformat(
                        timespec='seconds')
                    order_date = datetime.today().date().isoformat()
                    order_date = datetime.strptime(order_date, '%Y-%m-%d').strftime('%Y.%m.%d')
                    order_timings.update({message.chat.id: (order_date, order_time)})

                    create_sys_orders_file()
                    create_orders_file(message)
                    write_order_in_db(message)
                    bot.send_message(message.chat.id, 'Ваш заказ оформлен!')
                    bot.send_message(message.chat.id,
                                     create_order_msg(message), reply_markup=create_buttons(lvl=0))
                    on_delete_order(message.chat.id)
                else:
                    bot.send_message(message.chat.id, 'Ваш заказ пуст')

            elif message.text == 'Обновить меню':
                tmpmenu, tmpdish_prices, tmpmenu_date, tmpmenu_date_obj, tmpdish_info = {}, {}, '', None, {}

                with open('menu.txt', 'r', encoding='utf-8') as menu_file:
                    lines = menu_file.readlines()
                    tmpmenu_date = f'{day_of_week(lines[0][:-1])} {lines[0][:-1]} '
                    tmpmenu_date_obj = datetime.strptime(lines[0][:-1], "%d.%m.%Y")
                    category = ''
                    for line in lines[1:]:
                        line = line.strip()
                        if line.startswith('[') and line.endswith(']'):
                            category = line[1:-1]
                            if category == 'Первые блюда':
                                category = '🍲 ' + category
                            elif category == 'Вторые блюда':
                                category = '🍗 ' + category
                            elif category == 'Гарниры':
                                category = '🍝 ' + category
                            elif category == 'Салаты':
                                category = '🥗 ' + category
                            elif category == 'Zoom завтраки':
                                category = '🥞 ' + category
                            tmpmenu.update({category: {}})
                        elif line.startswith('Описание;'):
                            tmpdish_info.update({dish_name: line[line.index(';') + 1:]})
                        else:
                            dish_name, dish_price = line.split(';')
                            tmpmenu[category].update({dish_name: float(dish_price)})
                menu_file.close()
                for i in list(tmpmenu.values()):
                    tmpdish_prices.update(i)
                if menu != tmpmenu:
                    menu = tmpmenu
                    dish_prices = tmpdish_prices
                    menu_date, menu_date_obj, dish_info = tmpmenu_date, tmpmenu_date_obj, tmpdish_info
                    all_orders, totals, order_timings = {}, {}, {}
                bot.send_message(message.chat.id, create_message_menu(),
                                 parse_mode='Markdown', reply_markup=create_buttons())

            elif message.text.startswith('send') and message.chat.id in admins:
                send_time = message.text.split(' ')[1]

            elif message.text == 'check send' and message.chat.id in admins:
                bot.send_message(message.chat.id, f'Send time: {send_time}')

            elif message.text.startswith('Рассылка:'):
                if message.chat.id in admins or message.chat.id in cooks:
                    msg = message.text.split(':')[-1][1:]
                    recievers = []
                    for us in valid_users:
                        if us not in cooks:
                            recievers.append(us)
                    rassilka(recievers, msg)

            else:
                bot.send_message(message.chat.id, 'Что-то не так',
                                 reply_markup=create_buttons())

        else:  # Пользователь не авторизован и/или  у него роль повара
            if message.text == 'Регистрация' or message.text == 'Попробовать снова':
                authorization_request(message)
            elif message.text == 'Готово' and message.chat.id not in cooks:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton(text='Готово'))
                markup.add(types.KeyboardButton(text='Попробовать снова'))
                bot.send_message(message.chat.id, 'Попробуйте позже',
                                 reply_markup=markup)
            elif message.chat.id in cooks:
                bot.send_message(message.chat.id, 'Вы повар, можете отправлять'
                                                  ' файл с меню',
                                 reply_markup=types.ReplyKeyboardRemove())
            elif message.text == cook_pass and message.chat.id not in cooks:
                authorization_request(message, 'повар')
            elif message.text == admin_pass and message.chat.id not in admins:
                authorization_request(message, 'админ')
            else:  # проверка на пароли
                unknown_user(message.chat.id)

    except Exception as e:
        bot.send_message(admins[0], str(e))


# ____________Обработка файлов_________
# Повар отправляет меню
@bot.message_handler(content_types=['document'])
def download_menu_file(message):
    if message.chat.id in admins or message.chat.id in cooks:
        fname = 'menu.txt'
        if message.document.file_name == fname:
            # try parse file
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(fname, 'wb') as new_file:
                new_file.write(downloaded_file)
            new_file.close()
            # send_orders_file()
            init_menu()
            if message.chat.id in admins:
                bot.send_message(message.chat.id, 'Меню принято',
                                 reply_markup=create_buttons())
            else:
                bot.send_message(message.chat.id, 'Меню принято')
    else:
        bot.send_message(message.chat.id, 'Файл с меню могут '
                                          'отправлять только повара и админы')


# Логирование

# ______________________________Отправка заказов_________________________
send_time = '14:00'
send_users_table_day = 16


# Не работает, тк изменили бд
def increase_totals_in_db():
    global users_table_name, admins

    try:
        totals = get_orders_vars_from_sys()['Totals']
        cnx = get_connection()
        for user, price in totals.items():
            increase_func(cnx, users_table_name,
                          'total_in_month', 'total_in_month + ' + str(price),
                          f'user_tgid = {user};')
        cnx.close()
    except Exception as e:
        bot.send_message(admins[0], f'increase bad\n{e}')


# Не работает, тк изменили таблицу
def update_orders_table():
    global users_table_name, admins

    try:
        sys_orders, sys_order_timings, sys_totals, sys_dish_prices = \
            get_orders_vars_from_sys().values()

        orders_list = []
        for user in sys_orders:
            orders_list.append((user, sys_order_timings[user][0],
                                sys_order_timings[user][1], sys_totals[user]))
        insert(get_connection(), orders_table_name, orders_params, orders_list)
        rassilka(list(sys_orders.keys()), "Ваш заказ успешно отправлен!")

    except Exception as e:
        bot.send_message(admins[0], f'update_orders_table bad\n{e}')


# Отправляет файл orders.txt cooks[0] и добавляет сумму на счет
def send_orders_file():
    global cooks, admins, menu_date_obj, menu_date

    delta = menu_date_obj.date() - datetime.today().date()

    if delta.days == 1:
        if len(get_orders_vars_from_sys()['All orders']) == 0:
            bot.send_message(admins[0], f'Заказов на {menu_date} нет')
        else:
            increase_totals_in_db()
            update_orders_table()
            create_orders_file()
            bot.send_document(admins[0], document=open('orders.txt', 'rb'))  # Отправка заказов повару

            bot.send_message(admins[0], 'Заказы отправлены')

            f = open('orders.txt', 'w', encoding='utf-8')
            f.seek(0)
            f.close()

            f = open('sys_orders.txt', 'w', encoding='utf-8')
            f.seek(0)
            f.close()

            f = open('orders.txt', 'w', encoding='utf-8')
            f.write(f'{datetime.now()}')
            f.close()

            f = open('sys_orders.txt', 'w', encoding='utf-8')
            f.write(f'Bot file: {datetime.now()}')
            f.close()


def send_users_table_as_csv(recipient=admins[0]):
    global cooks, admins, users_table_name

    export_table_as_csv(get_connection(), users_table_name, 'users_table.csv')
    bot.send_document(recipient, document=open(f'users_table.csv', 'rb'))


# Функция, которая каждый месяц send_users_table_day числа
# отправляет файл с пользователями,
# очищает заказы из бд и total_in_month=0

def monthly_func():
    global cooks, admins, menu_date_obj, menu_date

    if datetime.today().day == send_users_table_day:
        send_users_table_as_csv()

        # Обнуление счета за месяц
        update(get_connection(), users_table_name, 'total_in_month', '0', 'total_in_month>0')

        # Очистка тааблицы с заказами
        delete(get_connection(), orders_table_name, 'order_id>0')


def main():
    try:
        global send_time, menu_date_obj

        # schedule.every().day.at(send_time).do(send_orders_file)
        while True:
            try:
                bot.polling(non_stop=True, interval=0)
            except Exception as e:
                print(e)
                time.sleep(5)
                continue
        # schedule.every().day.at((datetime.strptime(send_time, '%H:%M')
        #                          + timedelta(seconds=20)).time().isoformat()).do(monthly_func)
        # while True:
        #     schedule.run_pending()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
