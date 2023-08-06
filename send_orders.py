from lunchBot import *
import schedule

send_time = '17:01'


def increase_totals_in_db():
    global users_table_name

    try:
        totals = get_orders_vars_from_sys()['Totals']
        for user in totals:
            update(get_connection(), users_table_name, 'total_in_month', str(totals[user]), f'user_tgid = {user}')
    except Exception as e:
        bot.send_message(admins[0],f'increase bad\n{e}')


# Отправляет файл orders.txt cooks[0] и добавляет сумму на счет
def send_orders_file():
    global cooks, admins

    bot.send_message(admins[0],f"Totals: {get_orders_vars_from_sys()['Totals']}\n"
                               f"Type={type(get_orders_vars_from_sys()['Totals'])}\n"
                               f"Hasattr: {hasattr(get_orders_vars_from_sys()['Totals'],'__iter__')}")
    increase_totals_in_db()
    create_orders_file()
    bot.send_document(admins[0], document=open('orders.txt', 'rb'))  # Отправка заказов повару

    bot.send_message(admins[0], 'Заказы отправлены')
    # bot.send_message(admins[0], f'{all_orders}\n{totals}\n{order_timings}\n{cooks}\n{admins}')
    f = open('orders.txt', 'w', encoding='utf-8')
    f.seek(0)
    f.close()
    # Для проверки, тк пустой файл не отправляет
    f = open('orders.txt', 'w', encoding='utf-8')
    f.write(f'{datetime.now()}')
    f.close()


def send_orders():
    global admins

    bot.send_message(admins[0],f'All orders: {all_orders}')


def main():
    global send_time
    schedule.every().day.at(send_time).do(send_orders_file)
    # schedule.every(10).seconds.do(send_orders)
    while True:
        schedule.run_pending()


if __name__ == '__main__':
    main()
