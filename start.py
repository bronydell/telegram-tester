import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import answers
from actions import super_actions


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)


def error_callback(bot, update, error):
    try:
        raise error
    except TelegramError:
        print(type(error))


if __name__ == "__main__":
    with open('key.config', 'r', encoding='utf-8') as myfile:
        key = myfile.read().replace('\n', '')

    updater = Updater(key)

    updater.dispatcher.add_handler(MessageHandler(Filters.document | Filters.text | Filters.photo | Filters.audio,
                                                  answers.answer))
    updater.dispatcher.add_handler(CallbackQueryHandler(answers.click))
    updater.dispatcher.add_handler(CommandHandler('start', answers.def_menu))
    updater.dispatcher.add_error_handler(error_callback)
    updater.start_polling()
    updater.idle()
