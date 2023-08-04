import telebot
from telebot import types
from datetime import datetime

bot = telebot.TeleBot('6491551409:AAEprVBKNaPqKEfIt33vCipdGCGn_aOCbQI')

# Хранятся заказы в виде:
# {user_id1: {dish1: num1, ...}, user_id2: {dish4: num3, ...}, ...}
all_orders = {}

# Хранятся суммы заказов
# {user_id1: total1, user_id2: total2,...}
totals = {}

# Меню в виде
# {category1: {dish1: price1, dish2: price2, ...}, ...}
menu = {}

# Все блюда подряд: {dish1: price1, dish2: price2, ...}
allDishes = {}

with open('menu.txt', 'r', encoding='utf-8') as menu_file:
    lines = menu_file.readlines()
    category = ''
    for line in lines:
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
        else:
            dish_name, dish_price = line.split(':')
            menu[category].update({dish_name: float(dish_price)})
menu_file.close()

dishies = list(menu.values())
for i in dishies:
    allDishes.update(i)


def create_menu(message_text=None, user_id=None):
    back_btn = types.KeyboardButton('◀ Назад️')
    confirm_btn = types.KeyboardButton(text='✅ Оформить заказ')
    remove_btn = types.KeyboardButton(text='❌ Режим удаления')
    clear_btn = types.KeyboardButton(text='🗑 Удалить все')

    if message_text is None and user_id is None:  # Create start menu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        btn_arr = []

        for m in menu:
            btn_arr.append(types.KeyboardButton(text=f'{m}'))
        markup.add(*btn_arr)
        markup.row(confirm_btn, remove_btn, clear_btn)
        return markup
    elif message_text is not None:  # Create submenu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for dish, price in menu[message_text].items():
            markup.add(types.KeyboardButton(text=f'{dish} - {price}'))

        markup.add(back_btn)
        return markup
    else:  # Create remove mode menu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn_arr = []
        for dish, num in all_orders[user_id].items():
            btn_arr.append(types.KeyboardButton(text=f'{dish}    x{num}'))
        markup.add(*btn_arr)
        markup.add(back_btn)
        return markup


def create_order_msg(message):
    global all_orders, totals, allDishes

    msg = 'Ваш заказ:\n'
    total_price = 0
    for dish, num in all_orders[message.from_user.id].items():
        price = allDishes[dish]
        msg += f'{dish} -- {price}p.  x{num}\n'
        total_price += price * num
        total_price = round(total_price, 2)
    msg += f'\nИтого: {total_price}p.'
    totals.update({message.from_user.id: total_price})
    return msg


def create_order_file():
    global all_orders, totals

    f = open('orders.txt', 'w', encoding='utf-8')
    for user in all_orders:
        f.write(f'Пользователь {user} заказал:\n')
        for dish, num in all_orders[user].items():
            f.write(f'{dish}    x{num}\n')
        f.write(f'\nИтого: {totals[user]}\n')
        f.write(f'Дата: {datetime.today().date().isoformat()}\n')
        order_time = datetime.today().time().isoformat(
            timespec='seconds')
        f.write(f'Время: {order_time}')
        f.write('\n_______________\n\n')
    f.close()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Здравствуйте, '
                                      f'{message.from_user.first_name}',
                     reply_markup=create_menu())


# Обработка поступающих сообщений
@bot.message_handler(content_types=['text'])
def bot_message(message):
    global menu, all_orders, totals, allDishes

    if message.chat.type == 'private':
        if message.text in menu:
            bot.send_message(message.chat.id, message.text,
                             reply_markup=create_menu(
                                 message_text=message.text))

        elif message.text == '◀ Назад️':
            bot.send_message(message.chat.id, '◀ Назад️',
                             reply_markup=create_menu())

        elif message.text.split('-')[0].strip() in allDishes:
            dish = message.text.split('-')[0].strip()
            if message.from_user.id in all_orders:
                if dish in all_orders[message.from_user.id]:
                    all_orders[message.from_user.id][dish] += 1
                else:
                    all_orders[message.from_user.id].update({dish: 1})
            else:
                all_orders.update({message.from_user.id: {dish: 1}})
            bot.send_message(message.chat.id, f'{dish} добавлен')
            bot.send_message(message.chat.id, create_order_msg(message))

        elif message.text.split('x')[0].strip() in allDishes:
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
            create_order_file()
            bot.send_message(message.chat.id, 'Очищено!')

        elif message.text == '❌ Режим удаления':
            bot.send_message(message.chat.id, 'Удалите что-либо',
                             reply_markup=create_menu(
                                 user_id=message.from_user.id))

        elif message.text == '✅ Оформить заказ':
            if message.from_user.id in all_orders:
                create_order_file()
                bot.send_message(message.chat.id, 'Заказ оформлен!')
            else:
                bot.send_message(message.chat.id, 'Ваш заказ пуст')

        else:
            bot.send_message(message.chat.id, 'Что-то не так')


bot.polling()
