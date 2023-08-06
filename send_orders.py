from lunchBot import *
import schedule


send_time = '19:24'

def increase_totals_in_db():
    global users_table_name, admins

    try:
        totals = get_orders_vars_from_sys()['Totals']
        for user, price in totals.items():
            increase_func(get_connection(), users_table_name,
                          'total_in_month', 'total_in_month + ' + str(price),
                          f'user_tgid = {user};')
    except Exception as e:
        bot.send_message(admins[0], f'increase bad\n{e}')


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

    except Exception as e:
        bot.send_message(admins[0], f'update_orders_table bad\n{e}')


# Отправляет файл orders.txt cooks[0] и добавляет сумму на счет
def send_orders_file():
    global cooks, admins

    # bot.send_message(admins[0],f"Totals: {get_orders_vars_from_sys()['Totals']}\n"
    #                            f"Type={type(get_orders_vars_from_sys()['Totals'])}\n"
    #                            f"Hasattr: {hasattr(get_orders_vars_from_sys()['Totals'],'__iter__')}")
    increase_totals_in_db()
    update_orders_table()
    create_orders_file()
    bot.send_document(admins[0], document=open('orders.txt', 'rb'))  # Отправка заказов повару

    bot.send_message(admins[0], 'Заказы отправлены')
    # bot.send_message(admins[0], f'{all_orders}\n{totals}\n{order_timings}\n{cooks}\n{admins}')
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







def send_orders():
    global admins

    bot.send_message(admins[0], f'All orders: {all_orders}')


def main():
    global send_time
    schedule.every().day.at(send_time).do(send_orders_file)
    # schedule.every(10).seconds.do(send_orders)
    while True:
        schedule.run_pending()


if __name__ == '__main__':
    main()
