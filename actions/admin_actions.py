from actions import super_actions
from db import Admin, User
from pony import orm
import telegram
import logging
from telegram.error import Unauthorized, RetryAfter
import time
from shutil import move
import json


def is_json(myjson):
    """JSON validation

        Parameters
        ----------
        myjson : str
            Bot provided by wrapper
        Returns
        -------
        bool
            Is valid?
        """
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


@orm.db_session
def replace_settings(bot, update, filename):
    """Replace json files. It validates JSON and replaces if everything is right

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        filename: str
            Filename of replacing files
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    settings = super_actions.get_bot_settings(user.lang_file)
    if update.message.document and Admin.exists(id=user.id):
        move(filename + '.json', filename + '_old' + '.json')
        file_id = update.message.document.file_id
        bot.getFile(file_id).download(filename + '.json')
        with open(filename + '.json', 'r', encoding='UTF-8') as content_file:
            if not is_json(content_file.read()):
                move(filename + '_old' + '.json', filename + '.json')
                update.effective_message.reply_text(settings['system_messages']['json_bot_not_valid'])
                logging.debug("User didn't {} replace {} with his own because of"
                              " the wrong JSON".format(user.id, filename))
            else:
                update.effective_message.reply_text(settings['system_messages']['json_bot_valid'])
                logging.debug("User {} replaced {} with his own".format(user.id, filename))
                admin_menu(bot, update, 'admin_panel')
        return True
    return False


@orm.db_session
def send_to_everyone(bot, update, txt):
    """Sends message to every user

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        txt: str
            Text to send
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    settings = super_actions.get_bot_settings(user.lang_file)
    if Admin.exists(id=user.id):
        logging.debug("User {} sent {} to all users".format(user.id, txt))
        for user in User.select():
            send_message(bot, update, user.id, text=txt)
        return True
    else:
        bot.sendMessage(update.message.chat_id, text=settings['system_messages']['not_admin'])
        return False


def send_message(bot, update, user, text=""):
    """Sends message to specific user

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        user: int
            Recipient's ID
        text: str
            Text to send
        Returns
        -------
        bool
            Is everything went fine?
        """
    try:
        bot.sendMessage(chat_id=user, text=text)
        time.sleep(0.1)
        return True
    except Unauthorized:
        return False
        pass
    except RetryAfter as ex:
        time.sleep(ex.retry_after)
        return send_message(bot, update, user, text=text)
    except Exception as ex:
        return False
        pass


@orm.db_session
def admin_menu(bot, update, act):
    """Opens menu that can open ONLY ADMIN

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        act: str
            Menu tag
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    settings = super_actions.get_bot_settings(user.lang_file)
    if Admin.exists(id=user.id):
        user.action = act
        logging.debug("User {} opened {} as admin".format(user.id, act))
        bot.sendMessage(user.id, text=settings[act]['message'],
                        reply_markup=telegram.ReplyKeyboardMarkup(keyboard=super_actions.get_keyboard(act, user.id)))
        return True
    else:
        logging.debug("User {} didn't open menu because he isn't admin".format(user.id))
        bot.sendMessage(user.id, text=settings['system_messages']['not_admin'])
        return False


@orm.db_session
def edit_preference(bot, update):
    """Sends JSON file to admin and waits for new  edited file

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    settings = super_actions.get_bot_settings(user.lang_file)
    if Admin.exists(id=user.id):
        act = 'edit_prefs'
        user.action = act
        logging.debug("User {} got file {} as admin".format(user.id, "bot.json"))
        bot.sendMessage(user.id, text=settings[act]['message'],
                        reply_markup=telegram.ReplyKeyboardMarkup(keyboard=super_actions.get_keyboard(act, user.id)))
        bot.sendDocument(user.id, document=open('bot.json', 'rb'))
        return True
    else:
        logging.debug("User {} didn't receive setting file because he isn't admin".format(user.id))
        bot.sendMessage(user.id, text=settings['system_messages']['not_admin'])
        return False
