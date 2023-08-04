import telebot
from telebot import types

bot = telebot.TeleBot('TOKEN')

user_orders = {}
user_prices = {}
menu = {}
allDishes = {}
remove_mode = 0

with open('menu.txt','r', encoding = 'utf-8') as f:
    lines = f.readlines()
    category = ''
    for line in lines:
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            category = line[1:-1]
            menu[category] = {}
        else:
            dish_name, dish_price = line.split(':')
            menu[category].update({dish_name: float(dish_price)})


dishies = list(menu.values())
for i in dishies:
    allDishes.update(i)


def create_menu(message_text=None, user_id=None):
    back = types.KeyboardButton('Back')
    
    if message_text is None and user_id is None:  # Create start menu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        btn_arr = []
        
        for m in menu:
            btn_arr.append(types.KeyboardButton(text=f'{m}'))
        markup.add(*btn_arr)
        markup.add(types.KeyboardButton(text='Confirm order'))
        markup.add(types.KeyboardButton(text='Remove mode'))
        markup.add(types.KeyboardButton(text='Clear all'))
        return markup
    elif message_text is not None:  # Create submenu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for el in menu[message_text]:
            markup.add(types.KeyboardButton(text=f'{el} - {menu[message_text][el]}'))

        markup.add(back)
        return markup
    else:  # Create remove mode menu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn_arr = []
        for m in user_orders[user_id]:
            btn_arr.append(types.KeyboardButton(text=f'{m}    x{user_orders[user_id][m]}'))
        markup.add(*btn_arr)
        markup.add(back)
        return markup


def create_order_msg(message):
    global user_orders, user_prices, allDishes
    msg = 'Your order:\n'
    total_price = 0
    for dish in user_orders[message.from_user.id]:
        msg += f'{dish} -- {allDishes[dish]}p.  x{user_orders[message.from_user.id][dish]}\n'
        total_price += allDishes[dish] * user_orders[message.from_user.id][dish]
        total_price = round(total_price, 2)
    msg += f'\nTotal price: {total_price}p.'
    user_prices.update({message.from_user.id: total_price})
    return msg


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Hello, {message.from_user.first_name}",
                     reply_markup=create_menu())


@bot.message_handler(content_types=['text'])
def bot_message(message):
    global remove_mode, menu, user_orders, user_prices, allDishes

    if message.chat.type == 'private':
        if message.text in menu:
            bot.send_message(message.chat.id, message.text, reply_markup=create_menu(message_text=message.text))

        elif message.text == 'Back':
            if remove_mode == 1:
                remove_mode = 0
            bot.send_message(message.chat.id, 'Back', reply_markup=create_menu())

        elif message.text.split('-')[0].strip() in allDishes:
            dish_name = message.text.split('-')[0].strip()
            if message.from_user.id in user_orders:
                if dish_name in user_orders[message.from_user.id]:
                    user_orders[message.from_user.id][dish_name] += 1
                else:
                    user_orders[message.from_user.id].update({dish_name: 1})
            else:
                user_orders.update({message.from_user.id: {dish_name: 1}})
            bot.send_message(message.chat.id, f'{dish_name} added')
            bot.send_message(message.chat.id, create_order_msg(message))

        elif message.text.split('x')[0].strip() in allDishes:
            dish_name = message.text.split('x')[0].strip()
            user_orders[message.from_user.id][dish_name] -= 1
            if user_orders[message.from_user.id][dish_name] == 0:
                del user_orders[message.from_user.id][dish_name]
            if user_orders[message.from_user.id] == {}:
                del user_orders[message.from_user.id]
                del user_prices[message.from_user.id]
            bot.send_message(message.chat.id, f'1 {dish_name} deleted',
                             reply_markup=create_menu(user_id=message.from_user.id))
            bot.send_message(message.chat.id, create_order_msg(message))

        elif message.text == 'Clear all':
            del user_orders[message.from_user.id]
            del user_prices[message.from_user.id]
            bot.send_message(message.chat.id, 'Cleared!')

        elif message.text == 'Remove mode':
            remove_mode = 1
            bot.send_message(message.chat.id, 'Remove something!',
                             reply_markup=create_menu(user_id=message.from_user.id))

        elif message.text == 'Confirm order':
            f = open('orders.txt', 'w')
            for user in user_orders:
                f.write(f'\nUser {user} ordered:\n')
                for dish in user_orders[user]:
                    f.write(f'{dish}    x{user_orders[user][dish]}\n')
                f.write(f'Total: {user_prices[user]}')
                f.write('\n_______________\n')
            bot.send_message(message.chat.id, 'Order confirmed!')
            
        else:
            bot.send_message(message.chat.id, 'Something wrong')


bot.polling()
