from lunchBot import *
from send_orders import test
import schedule


def main():
    bot.polling()


# schedule.every().day.at('17:24').do(send_test_msg)
# schedule.every(30).seconds.do(send_order)
# while True:
#     schedule.run_pending()


if __name__ == '__main__':
    main()
