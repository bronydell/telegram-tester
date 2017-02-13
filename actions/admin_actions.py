from actions import super_actions
from database import user_db as udb
import telegram
import saver
from shutil import move
import json


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


def replaceSettings(bot, update, filename):
    settings = super_actions.getBotSettings()
    if update.message.document:
        move(filename + '.json', filename + '_old' + '.json')
        file_id = update.message.document.file_id
        bot.getFile(file_id).download(filename + '.json')
        with open(filename + '.json', 'r', encoding='UTF-8') as content_file:
            if not is_json(content_file.read()):
                move(filename + '_old' + '.json', filename + '.json')
                bot.sendMessage(update.message.chat_id, text=settings['system_messages']['json_bot_not_valid'])
            else:
                bot.sendMessage(update.message.chat_id, text=settings['system_messages']['json_bot_valid'])
                magic(bot, update, 'admin_panel')


def sendtoAll(bot, update, txt):
    settings = super_actions.getBotSettings()
    if saver.isAdmin(update.message.from_user.id):
        for user in udb.getAllUsers():
            try:
                bot.sendMessage(user, text=txt)
            except telegram.TelegramError as ex:
                bot.sendMessage(update.message.from_user.id, text='Произошла ошибка: ' + str(ex.message))
    else:
        bot.sendMessage(update.message.chat_id, text=settings['system_messages']['not_admin'])


def magic(bot, update, act):
    uid = update.message.from_user.id
    settings = super_actions.getBotSettings(uid)
    if saver.isAdmin(uid):
        udb.setUserAction(uid, act)
        bot.sendMessage(update.message.chat_id, text=settings[act]['message'],
                        reply_markup=telegram.ReplyKeyboardMarkup(keyboard=super_actions.getKeyboard(act, uid)))
    else:
        bot.sendMessage(update.message.chat_id, text=settings['system_messages']['not_admin'])


def editPrefs(bot, update):
    uid = update.message.from_user.id
    settings = super_actions.getBotSettings(uid)
    if saver.isAdmin(uid):
        act = 'edit_prefs'
        udb.setUserAction(uid, act)
        bot.sendMessage(update.message.chat_id, text=settings[act]['message'],
                        reply_markup=telegram.ReplyKeyboardMarkup(keyboard=super_actions.getKeyboard(act, uid)))
        bot.sendDocument(update.message.chat_id, document=open('bot.json', 'rb'))
    else:
        bot.sendMessage(update.message.chat_id, text=settings['system_messages']['not_admin'])
