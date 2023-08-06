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
        rassilka(list(sys_orders.keys()), "Ваш заказ был отправлен")

    except Exception as e:
        bot.send_message(admins[0], f'update_orders_table bad\n{e}')





# Отправляет файл orders.txt cooks[0] и добавляет сумму на счет
def send_orders_file():
    global cooks, admins, menu_date_obj

    delta = menu_date_obj.date() - datetime.today().date()
    if delta.days == 1:
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


# Функция, которая каждый месяц отправляет файл с пользователями,
# очищает заказы из бд и total_in_month=0
def send_user_totals():
    pass


def main():
    try:
        global send_time, menu_date_obj
        schedule.every().day.at(send_time).do(send_orders_file)

        # Добавить schedule для send_user_totals
        while True:
            schedule.run_pending()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()
