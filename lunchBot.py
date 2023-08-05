import telebot
from telebot import types
from datetime import datetime
from db_bot_funcs import *
from send_orders import send_orders_file

bot = telebot.TeleBot('6491551409:AAEprVBKNaPqKEfIt33vCipdGCGn_aOCbQI')

# Получаем из бд
valid_users = []
admins = []
cookers = []
admin_pass = 'oaq873ergf'
cooker_pass = 'zRgcu*T{zB'


def update_users():
    global valid_users, cookers, admins

    cnx = get_connection()
    valid_users = get_all_users_id_as_list(cnx, users_table_name)
    cookers = get_all_users_id_as_list(cnx, users_table_name, 'cook')
    # cookers.append(589562037)
    admins = get_all_users_id_as_list(cnx, users_table_name, 'admin')


update_users()

# Хранятся заказы в виде:
# {user_id1: {dish1: num1, ...}, user_id2: {dish4: num3, ...}, ...}
all_orders = {}

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


def init_menu():
    global menu, dish_prices, menu_date, menu_date_obj, dish_info
    menu, dish_prices, menu_date, menu_date_obj, dish_info = {}, {}, '', None, {}

    with open('menu.txt', 'r', encoding='utf-8') as menu_file:
        lines = menu_file.readlines()
        menu_date = f'{lines[0][:-1]} {day_of_week(lines[0][:-1])}'
        menu_date_obj = datetime.strptime(lines[0][:-1], "%d.%m.%Y")
        category = ''
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                category = line[1:-1]
                if category == 'Супы':
                    category = '🍜 ' + category
                elif category == 'Второе':
                    category = '🍛 ' + category
                elif category == 'Салаты':
                    category = '🥗 ' + category
                elif category == 'Напитки':
                    category = '☕ ' + category
                menu.update({category: {}})
                # menu[category] = {}
            elif line.startswith('Состав;'):
                dish_info[dish_name].append(line[line.index(';') + 1:])
            else:
                if len(line.split(';')) == 3:
                    dish_name, dish_mass, dish_price = line.split(';')
                    dish_info.update({dish_name: [dish_mass, ]})
                elif len(line.split(';')) == 2:
                    dish_name, dish_price = line.split(';')
                    dish_info.update({dish_name: []})
                menu[category].update({dish_name: float(dish_price)})
    menu_file.close()
    for i in list(menu.values()):
        dish_prices.update(i)


init_menu()


def create_buttons(message_text=None, user_id=None):
    back_btn = types.KeyboardButton('◀ Назад️')
    confirm_btn = types.KeyboardButton(text='✅ Оформить заказ')
    remove_btn = types.KeyboardButton(text='❌ Режим удаления')
    clear_btn = types.KeyboardButton(text='🗑 Удалить все')

    if message_text is None and user_id is None:  # Создание главного меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        markup.add(types.KeyboardButton(text='Показать меню'))
        btn_arr = []
        for m in menu:
            btn_arr.append(types.KeyboardButton(text=f'{m}'))
        markup.add(*btn_arr)
        markup.row(confirm_btn, remove_btn, clear_btn)
        return markup
    elif message_text is not None:  # Создание меню второго уровня
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for dish, price in menu[message_text].items():
            markup.add(types.KeyboardButton(text=f'{dish}: {price}'))

        markup.add(back_btn)
        return markup
    else:  # Создание меню в режиме удаления
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn_arr = []
        for dish, num in all_orders[user_id].items():
            btn_arr.append(types.KeyboardButton(text=f'{dish}    x{num}'))
        markup.add(*btn_arr)
        markup.add(back_btn)
        return markup


# Создает сообщение с текущим заказом
def create_order_msg(message):
    global all_orders, totals, dish_prices

    msg = 'Ваш заказ:\n'
    total_price = 0
    for dish, num in all_orders[message.from_user.id].items():
        price = dish_prices[dish]
        msg += f'{dish} -- {price}p.  x{num}\n'
        total_price += price * num
        total_price = round(total_price, 2)
    msg += f'\nИтого: {total_price}p.'
    totals.update({message.from_user.id: total_price})
    return msg


# Записывает заказы в файл
def create_orders_file():
    global all_orders, totals, order_timings

    f = open('orders.txt', 'w', encoding='utf-8')
    for user in all_orders:
        (order_date, order_time) = order_timings[user]
        f.write(f'Заказ {order_date} {order_time}; {user}\n')
        for dish, num in all_orders[user].items():
            f.write(f'{dish};{num};{dish_prices[dish]}\n')
        f.write(f'Итого: {totals[user]}')
        f.write('\n_______________\n\n')
    f.close()


# Функция кнопки "Показать меню"
def create_message_menu():
    global menu, dish_info, dish_prices, menu_date

    msg = f'Меню на {menu_date}:'
    msg += '\n'
    for categ in menu:
        msg += f'\n*{categ}*\n'
        for dish, price in menu[categ].items():
            msg += f'{dish} -- {price}\n'
            info = ''
            for s in dish_info[dish]:
                info += f'{s}; '
            if info != '':
                msg += f'{info}\n'
    return msg


# Создает сообщение для неавторизованного пользователя
def unknown_user(us_id):
    global bot
    bot.send_message(us_id, 'Упс, неопознаный пользователь')
    msg = 'Хотите авторизоваться?\nНажмите "Да", чтобы отправить свой' \
          ' id администратору'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='Да'))
    markup.add(types.KeyboardButton(text='Нет'))
    bot.send_message(us_id, msg, reply_markup=markup)


# Функция для отправки админу уведомления о новом пользователе
def authorization_request(message, role='пользователь', recipient=admins[0]):
    msg = f'Новый {role} хочет авторизоваться\n' \
          f'Name: {message.from_user.first_name} {message.from_user.last_name}\n' \
          f'Username: {message.from_user.username}\n' \
          f'id: {message.from_user.id}'
    bot.send_message(recipient, msg)
    msg = f'Запрос в роли {role} отправлен'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='Готово'))
    markup.add(types.KeyboardButton(text='Готово'))
    bot.send_message(message.chat.id, msg, reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    global valid_users

    if message.chat.id in valid_users:
        bot.send_message(message.chat.id, f'Здравствуйте, '
                                          f'{message.from_user.first_name}',
                         reply_markup=create_buttons())
    else:
        unknown_user(message.chat.id)


# _________Обработка команды /stop
@bot.message_handler(commands=['stop'])
def start(message):
    global users_table_name

    delete(get_connection(), users_table_name, f'user_tgid={message.chat.id}')
    bot.send_message(message.chat.id, 'Вы были удалены из базы данных LunchBot')


# Обработка поступающих сообщений
@bot.message_handler(content_types=['text'])
def bot_message(message):
    global menu, all_orders, totals, dish_prices, valid_users, admins, \
        cookers, menu_date, order_timings

    update_users()

    if message.chat.id in valid_users and message.chat.id not in cookers:  # Пользователь авторизован и роль не повар

        delta = menu_date_obj.date() - datetime.now().date()
        if delta.days > 0 and datetime.now().hour < 24:  # Проверка по времени
            if message.text in menu:
                bot.send_message(message.chat.id, message.text,
                                 reply_markup=create_buttons(
                                     message_text=message.text))

            elif message.text == '◀ Назад️' or message.text == 'Готово':
                bot.send_message(message.chat.id, message.text,
                                 reply_markup=create_buttons())

            elif message.text.split(':')[0].strip() in dish_prices:
                dish = message.text.split(':')[0].strip()
                if message.from_user.id in all_orders:
                    if dish in all_orders[message.from_user.id]:
                        all_orders[message.from_user.id][dish] += 1
                    else:
                        all_orders[message.from_user.id].update({dish: 1})
                else:
                    all_orders.update({message.from_user.id: {dish: 1}})
                bot.send_message(message.chat.id, f'{dish} добавлен')
                bot.send_message(message.chat.id, create_order_msg(message))

            elif message.text.split('x')[0].strip() in dish_prices:
                dish = message.text.split('x')[0].strip()
                all_orders[message.from_user.id][dish] -= 1

                if all_orders[message.from_user.id][dish] == 0:
                    del all_orders[message.from_user.id][dish]

                if all_orders[message.from_user.id] == {}:
                    del all_orders[message.from_user.id]
                    del totals[message.from_user.id]
                    bot.send_message(message.chat.id, 'Заказ пуст',
                                     reply_markup=create_buttons())
                else:
                    bot.send_message(message.chat.id, f'1 {dish} удален',
                                     reply_markup=create_buttons(
                                         user_id=message.from_user.id))
                    bot.send_message(message.chat.id, create_order_msg(message))

            elif message.text == '🗑 Удалить все':
                del all_orders[message.from_user.id]
                del totals[message.from_user.id]
                create_orders_file()
                bot.send_message(message.chat.id, 'Очищено!')

            elif message.text == '❌ Режим удаления':
                bot.send_message(message.chat.id, 'Удалите что-либо',
                                 reply_markup=create_buttons(
                                     user_id=message.from_user.id))

            elif message.text == '✅ Оформить заказ':
                if message.from_user.id in all_orders:
                    order_time = datetime.today().time().isoformat(
                        timespec='seconds')
                    order_date = datetime.today().date().isoformat()
                    order_date = datetime.strptime(order_date, '%Y-%m-%d').strftime('%Y.%m.%d')
                    order_timings.update({message.from_user.id: (order_date, order_time)})
                    create_orders_file()
                    bot.send_message(message.chat.id, 'Заказ оформлен!')
                else:
                    bot.send_message(message.chat.id, 'Ваш заказ пуст')

            elif message.text == 'Показать меню':
                bot.send_message(message.chat.id, create_message_menu(), parse_mode='Markdown')

            else:
                bot.send_message(message.chat.id, 'Что-то не так', reply_markup=create_buttons())
        elif message.text == 'Очистить заказы' and message.chat.id in admins:
            all_orders = {}
            totals = {}
            order_timings = {}
        else:
            bot.send_message(message.chat.id, 'В данное время заказы не принимаются')

    else:  # Пользователь не авторизован и/или  у него роль повара
        if message.text == 'Да':
            authorization_request(message)
        elif message.text == 'Готово' and message.chat.id not in cookers:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton(text='Готово'))
            markup.add(types.KeyboardButton(text='Готово'))
            bot.send_message(message.chat.id, 'Попробуйте позже',
                             reply_markup=markup)
        elif message.chat.id in cookers:
            bot.send_message(message.chat.id, 'Вы повар, можете отправлять'
                                              ' файл с меню',
                             reply_markup=types.ReplyKeyboardRemove())
        elif message.text == cooker_pass and message.chat.id not in cookers:
            authorization_request(message, 'повар')
        elif message.text == admin_pass and message.chat.id not in admins:
            authorization_request(message, 'админ')
        else:  # проверка на пароли
            unknown_user(message.chat.id)


# ____________Обработка файлов_________
# Повар отправляет меню
@bot.message_handler(content_types=['document'])
def download_menu_file(message):
    if message.chat.id in admins or message.chat.id in cookers:
        fname = 'menu.txt'
        if message.document.file_name == fname:
            # try parse file
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(fname, 'wb') as new_file:
                new_file.write(downloaded_file)
            new_file.close()
            send_orders_file()
            init_menu()
            if message.chat.id in admins:
                bot.send_message(message.chat.id, 'Меню принято', reply_markup=create_buttons())
            else:
                bot.send_message(message.chat.id, 'Меню принято')
    else:
        bot.send_message(message.chat.id, 'Файл с меню могут отправлять только повара и админы')