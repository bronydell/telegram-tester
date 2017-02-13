import json
import telegram
import database.user_db as udb
import numpy as np
import saver

locales = {
    'Русский язык':'bot.json',
    'Белорусский язык': 'bot_by.json'
}

def setLocale(uid, message):
    if message in locales:
        saver.savePref(uid, 'locale', locales[message])

def getLocale(uid):
    return saver.openPref(uid, 'locale', 'bot.json')

def getLangs(bot, update):
    uid = update.message.from_user.id
    menu = np.array([])
    settings = getBotSettings(uid)
    for key, value in locales.items():
        menu = np.append(menu, key)
    menu = np.reshape(menu, (-1, 1))
    udb.setUserAction(uid, 'pick_language')
    bot.sendMessage(uid, text=settings['system_messages']['pick_lang'],
                    reply_markup=telegram.ReplyKeyboardMarkup(keyboard=menu))




def getKeyboard(tag, id):
    settings = getBotSettings(id)
    menu = np.array([])
    for option in settings[tag]['keyboard']:
        if 'admin_only' in option:
            if saver.isAdmin(id) or option['admin_only'] == False:
                menu = np.append(menu, option['text'])
        else:
            menu = np.append(menu, option['text'])
    return np.reshape(menu, (-1, 1))


def getBotSettings(uid):
    with open(getLocale(uid), encoding='UTF-8') as data_file:
        data = json.load(data_file)
    return data


def connect(bot, update):
    uid = update.message.from_user.id
    settings = getBotSettings(uid)
    bot.sendMessage(uid, text=settings['system_messages']['admin_info'])


def menu(bot, update, id = -1):
    if update.message:
        uid = update.message.from_user.id
    elif update.callback_query:
        uid = update.callback_query.from_user.id
    if not id == -1:
        uid = id
    settings = getBotSettings(uid)
    act = 'menu'
    udb.setUserAction(uid, settings['default_menu'])
    bot.sendMessage(uid, text=settings[act]['message'],
                    reply_markup=telegram.ReplyKeyboardMarkup(keyboard=getKeyboard(act, uid)))
