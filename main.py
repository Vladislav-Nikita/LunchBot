from lunchBot import *
# Отправка по расписанию в одном main не работает
# from send_orders import send_orders_file
# import schedule


def main():
    bot.polling()
    # schedule.every().day.at('17:24').do(send_orders_file)
    # schedule.every(7).seconds.do(send_orders_file)
    # while True:
    #     schedule.run_pending()


if __name__ == '__main__':
    main()
