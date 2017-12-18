import json
import telegram
import logging
from pony import orm
from telegram import Bot, Update
from db import User, Admin

locales = {
    'Русский язык': 'bot.json',
    'Белорусский язык': 'bot_by.json'
}


@orm.db_session
def set_locale(user, message):
    """This method changes user's language to selected.

            Parameters
            ----------
            user : User
                User from database that we're going to edit
            message : str
                Language name that EQUALS to one of locales keys
            Returns
            -------
            bool
                Is language equals to message?
            """
    if message in locales:
        user.lang_file = locales[message]
        return True
    return False


@orm.db_session
def get_languages(bot, update, n_cols=1):
    """This method sends to user list of available languages

                Parameters
                ----------
                bot : Bot
                    Bot provided by wrapper
                update : Update
                    Update provided by wrapper
                n_cols : int
                    Count of columns in buttons
                Returns
                -------
                bool
                    Is everything went fine?
                """
    user = User[update.effective_user.id]
    menu = []
    settings = get_bot_settings(user.lang_file)
    for key, value in locales.items():
        menu.append(key)
    menu = [menu[i:i + n_cols] for i in range(0, len(menu), n_cols)]
    user.action = "pick_language"
    bot.sendMessage(user.id, text=settings['system_messages']['pick_lang'],
                    reply_markup=telegram.ReplyKeyboardMarkup(keyboard=menu))
    return True


@orm.db_session
def get_keyboard(tag, uid, n_cols=1):
    """This method generates keyboard for menu

                Parameters
                ----------
                tag : str
                    Menu name
                uid : int
                    User's ID
                n_cols : int
                    Count of columns in buttons
                Returns
                -------
                list
                    List of buttons for menu
                """
    user = User[uid]
    settings = get_bot_settings(user.lang_file)
    menu = []
    for option in settings[tag]['keyboard']:
        if 'admin_only' in option:
            if Admin.exists(id=uid) or not option['admin_only']:
                menu.append(option['text'])
        else:
            menu.append(option['text'])
    return [menu[i:i + n_cols] for i in range(0, len(menu), n_cols)]


def get_bot_settings(filename="bot.json"):
    """This method reads settings file and returns it at dictionary

                    Parameters
                    ----------
                    filename : str
                        Settings filename
                    Returns
                    -------
                    dict
                        JSON dict read from file
                    """
    with open(filename, encoding='UTF-8') as data_file:
        data = json.load(data_file)
    return data


@orm.db_session
def del_last_msg(bot, user):
    if user.info.get('inline_id', -1) != -1:
        bot.delete_message(user.id, message_id=user.info['inline_id'])


@orm.db_session
def set_last_msg(message, user):
    user.info['inline_id'] = message


@orm.db_session
def default_menu(bot, update, uid=-1):
    """Show to user DEFAULT menu

    Parameters
    ----------
    bot : Bot
        Bot provided by wrapper
    update : Update
        Update provided by wrapper
    uid: int
        You can specify which user you will send to menu. It's useful for admin things
    Returns
    -------
    bool
        Is everything went fine?
    """
    if uid == -1:
        uid = update.effective_user.id
    if not User.exists(id=uid):
        user = User(id=uid,
                    action=get_bot_settings("bot.json")['default_menu'],
                    name=update.effective_user.first_name + " "+
                    update.effective_user.last_name if update.effective_user.last_name else "",
                    username=update.effective_user.username if update.effective_user.username else "",
                    lang_file="bot.json",
                    info={})
    else:
        user = User[uid]
    logging.debug("User {} went to default menu".format(user.id))
    settings = get_bot_settings(user.lang_file)
    act = "menu"
    user.action = settings['default_menu']
    bot.sendMessage(uid, text=settings[act]['message'],
                    reply_markup=telegram.ReplyKeyboardMarkup(keyboard=get_keyboard(act, uid)))
    return True
