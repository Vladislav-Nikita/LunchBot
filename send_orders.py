from lunchBot import *
from db_bot_funcs import users_table_name, orders_table_name
import schedule

send_time = '15:51'
send_users_table_day = 16


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
    global cooks, admins, menu_date_obj, menu_date

    delta = menu_date_obj.date() - datetime.today().date()

    if len(get_orders_vars_from_sys()['All orders']) == 0:
        bot.send_message(admins[0], f'Заказов на {menu_date} нет')
    elif delta.days == 1:
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

        schedule.every().day.at(send_time).do(send_orders_file)

        # schedule.every().day.at((datetime.strptime(send_time, '%H:%M')
        #                          + timedelta(seconds=20)).time().isoformat()).do(monthly_func)
        while True:
            schedule.run_pending()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
