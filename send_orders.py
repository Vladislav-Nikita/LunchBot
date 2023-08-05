from lunchBot import *
import schedule


# Отправляет файл orders.txt cookers[0]
def send_orders_file():
    global all_orders, totals, order_timings, cookers, admins

    bot.send_document(admins[0], document=open('orders.txt', 'rb'))  # Отправка заказов повару
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    markup.add(types.KeyboardButton(text='Очистить заказы'))
    markup.add(types.KeyboardButton(text='Очистить заказы'))
    bot.send_message(admins[0], 'Заказы отправлены', reply_markup=markup)
    all_orders = {}
    totals = {}
    order_timings = {}
    f = open('orders.txt', 'w', encoding='utf-8')
    f.seek(0)
    f.close()
    # Для проверки, тк пустой файл не отправляет
    f = open('orders.txt', 'w', encoding='utf-8')
    f.write(f'{datetime.now()}')
    f.close()


def main():
    schedule.every().day.at('14:00').do(send_orders_file)
    # schedule.every(10).seconds.do(send_orders_file)
    while True:
        schedule.run_pending()


if __name__ == '__main__':
    main()
