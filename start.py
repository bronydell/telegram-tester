import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import saver
import answers
from actions import super_actions
import sys
# sys.setdefaultencoding() does not exist, here!

sys.setdefaultencoding('UTF8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                  level=logging.DEBUG)


with open('key.config', 'r', encoding='utf-8') as myfile:
    key = myfile.read().replace('\n', '')


updater = Updater(key)
saver.initDataBase()

updater.dispatcher.add_handler(MessageHandler(Filters.document | Filters.text | Filters.photo | Filters.audio,
                                              answers.answer))
updater.dispatcher.add_handler(CallbackQueryHandler(answers.click))
updater.dispatcher.add_handler(CommandHandler('start', super_actions.menu))
updater.dispatcher.add_handler(CommandHandler('cancel', super_actions.menu))

updater.start_polling()
updater.idle()