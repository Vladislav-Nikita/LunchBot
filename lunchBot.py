import telebot
from telebot import types
from datetime import datetime
from db_bot_funcs import *
# import schedule

bot = telebot.TeleBot('6491551409:AAEprVBKNaPqKEfIt33vCipdGCGn_aOCbQI')

# Получаем из бд
valid_users = []
admins = []
cookers = []


def update_users():
    global valid_users, cookers, admins

    cnx = get_connection()
    valid_users = get_all_users_id_as_list(cnx, 'users')
    cookers = get_all_users_id_as_list(cnx, 'users', 'cook')
    cookers.append(589562037)
    admins = get_all_users_id_as_list(cnx, 'users', 'admin')


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

# Все блюда подряд: {dish1: price1, dish2: price2, ...}
dishPrices = {}

# Состав и граммовки блюд
# {dish1: [состав, граммовка]}
dish_info = {}

weekdays_list = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница',
                 'суббота', 'воскресенье']


def day_of_week(date_str):
    global weekdays_list
    return weekdays_list[datetime.strptime(date_str, "%d.%m.%Y").weekday()]


with open('menu.txt', 'r', encoding='utf-8') as menu_file:
    lines = menu_file.readlines()
    menu_date = f'{lines[0][:-1]} {day_of_week(lines[0][:-1])}'
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
            menu[category] = {}
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

dishes = list(menu.values())
for i in dishes:
    dishPrices.update(i)


def create_menu(message_text=None, user_id=None):
    back_btn = types.KeyboardButton('◀ Назад️')
    confirm_btn = types.KeyboardButton(text='✅ Оформить заказ')
    remove_btn = types.KeyboardButton(text='❌ Режим удаления')
    clear_btn = types.KeyboardButton(text='🗑 Удалить все')

    if message_text is None and user_id is None:  # Создание главного меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        markup.add(types.KeyboardButton(text='Показать меню'))
        btn_arr = []
        for m in menu:
            btn_arr.append(types.KeyboardButton(text=f'{m}'))
        markup.row(*btn_arr)
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
    global all_orders, totals, dishPrices

    msg = 'Ваш заказ:\n'
    total_price = 0
    for dish, num in all_orders[message.from_user.id].items():
        price = dishPrices[dish]
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
        (order_date,order_time) = order_timings[user]
        f.write(f'Заказ {order_date} {order_time}; {user}\n')
        for dish, num in all_orders[user].items():
            f.write(f'{dish};{num};{dishPrices[dish]}\n')
        f.write(f'Итого: {totals[user]}')
        f.write('\n_______________\n\n')
    f.close()


# Функция кнопки "Показать меню"
def create_message_menu():
    global menu, dish_info, dishPrices, menu_date

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
def unknown_user(id):
    global bot
    bot.send_message(id, 'Упс, неопознаный пользователь')
    msg = 'Хотите авторизоваться?\nНажмите "Да", чтобы отправить свой' \
          ' id администратору'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='Да'))
    markup.add(types.KeyboardButton(text='Нет'))
    bot.send_message(id, msg, reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    # if message.chat.type == 'private':
    #     bot.send_message(message.chat.id, f'Здравствуйте, '
    #                                       f'{message.from_user.first_name}',
    #                      reply_markup=create_menu())
    # Если добавлять пользователей из бд
    if message.chat.id in valid_users:
        bot.send_message(message.chat.id, f'Здравствуйте, '
                                          f'{message.from_user.first_name}',
                         reply_markup=create_menu())
    else:
        unknown_user(message.chat.id)
        # bot.send_message(message.chat.id, 'Упс, неопознаный пользователь')
        # msg = 'Хотите авторизоваться?\nНажмите "Да", чтобы отправить свой' \
        #       ' id администратору'
        # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        # markup.add(types.KeyboardButton(text='Да'))
        # markup.add(types.KeyboardButton(text='Нет'))
        #
        # bot.send_message(message.chat.id, msg, reply_markup=markup)


# Обработка поступающих сообщений
@bot.message_handler(content_types=['text'])
def bot_message(message):
    global menu, all_orders, totals, dishPrices, valid_users, admins, \
        cookers, menu_date

    update_users()

    if message.chat.id in valid_users:
        if message.text in menu:
            bot.send_message(message.chat.id, message.text,
                             reply_markup=create_menu(
                                 message_text=message.text))

        elif message.text == '◀ Назад️' or message.text == 'Готово':
            bot.send_message(message.chat.id, message.text,
                             reply_markup=create_menu())

        elif message.text.split(':')[0].strip() in dishPrices:
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

        elif message.text.split('x')[0].strip() in dishPrices:
            dish = message.text.split('x')[0].strip()
            all_orders[message.from_user.id][dish] -= 1

            if all_orders[message.from_user.id][dish] == 0:
                del all_orders[message.from_user.id][dish]

            if all_orders[message.from_user.id] == {}:
                del all_orders[message.from_user.id]
                del totals[message.from_user.id]
                bot.send_message(message.chat.id, 'Заказ пуст',
                                 reply_markup=create_menu())
            else:
                bot.send_message(message.chat.id, f'1 {dish} удален',
                                 reply_markup=create_menu(
                                     user_id=message.from_user.id))
                bot.send_message(message.chat.id, create_order_msg(message))

        elif message.text == '🗑 Удалить все':
            del all_orders[message.from_user.id]
            del totals[message.from_user.id]
            create_orders_file()
            bot.send_message(message.chat.id, 'Очищено!')

        elif message.text == '❌ Режим удаления':
            bot.send_message(message.chat.id, 'Удалите что-либо',
                             reply_markup=create_menu(
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
            bot.send_message(message.chat.id, 'Что-то не так')

    else:
        if message.text == 'Да':
            msg = f'Новый пользователь хочет авторизоваться\n' \
                  f'Name: {message.from_user.first_name} {message.from_user.last_name}\n' \
                  f'Username: {message.from_user.username}\n' \
                  f'id: {message.from_user.id}'
            bot.send_message(admins[0], msg)
            msg = 'Запрос отправлен'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton(text='Готово'))
            markup.add(types.KeyboardButton(text='Готово'))
            bot.send_message(message.chat.id, msg, reply_markup=markup)
        elif message.text == 'Готово':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton(text='Готово'))
            markup.add(types.KeyboardButton(text='Готово'))
            bot.send_message(message.chat.id, 'Попробуйте позже', reply_markup=markup)
        else:
            unknown_user(message.chat.id)


