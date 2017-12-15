import database.user_db as udb
from database import admin_db as adb
from actions import super_actions, admin_actions
from actions import test_actions as tests
import telegram
from telegram import TelegramError

def performIt(bot, update, action):
    if action == 'menu':
        super_actions.menu(bot, update)
    elif action == 'send_msg_all':
        admin_actions.magic(bot, update, 'send_msg_all')
    elif action == 'edit_prefs':
        admin_actions.editPrefs(bot, update)
    elif action == 'add_admin':
        admin_actions.magic(bot, update, 'add_admin')
    elif action == 'del_admin':
        admin_actions.magic(bot, update, 'del_admin')
    elif action == 'contact_admin':
        super_actions.connect(bot, update)
    elif action == 'admin':
        admin_actions.magic(bot, update, 'admin_panel')
    elif action == 'completed_tests':
        tests.completedTestList(bot, update)
    elif action == 'change_language':
        super_actions.getLangs(bot, update)
    elif action == 'test':
        # tests.start_test(bot, update, 'tests_data/1.json')
        tests.test_list(bot, update, 0)

def click(bot, update):
    try:
        uid = update.effective_user.id
        data = update.callback_query.data

        if data.startswith('answer'):
            answ = data.split(' ')
            tests.checkAnswer(bot, update, int(answ[1]))
            tests.nextQuestion(bot, update)
        elif data.startswith('back_menu'):
            bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                                text='Вы перешли в меню',
                                reply_markup=None)
            super_actions.menu(bot, update)

        elif data.startswith('back_testlist'):
            filename = data.split(' ')[1]
            tests.test_list(bot, update, filename, is_update=True)

        elif data.startswith('back_comptestlist'):
            filename = data.split(' ')[1]
            tests.completedTestList(bot, update, is_update=True)

        elif data.startswith('details_test'):
            splited = data.split(' ')
            filename = splited[1]
            source = splited[2]

            tests.test_details(bot, update, filename, source = source)


        elif data.startswith('start_test'):
            filename = data.split(' ')[1]
            test = tests.getTest(filename)
            bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                                    text='Вы начали проходить тест "{}" '.format(test['title']),
                                    reply_markup=None)
            tests.start_test(bot, update, filename)
    except TelegramError as te:
        print(te.message)




def answer(bot, update):
    try:
        uid = update.effective_user.id
        settings = super_actions.getBotSettings(uid)
        act = udb.getUserAction(update.message.from_user.id, settings['default_menu'])
        udb.setUserUsername(uid, update.message.from_user.username)
        if act in settings:
            for option in settings[act]['keyboard']:
                if option['text'] == update.message.text:
                    performIt(bot, update, option['action'])
                    return None
        elif act == 'pick_language':
            super_actions.setLocale(uid, update.message.text)
            super_actions.menu(bot, update)
        elif act == 'send_msg_all':
            admin_actions.sendtoAll(bot, update, update.message.text)
            admin_actions.magic(bot, update, 'admin_panel')
        elif act == 'edit_prefs':
            admin_actions.replaceSettings(bot, update, 'bot')
        elif act == 'add_admin':
            adb.appendAdmin(int(update.message.text))
            admin_actions.magic(bot, update, 'admin_panel')
        elif act == 'del_admin':
            adb.removeAdmin(int(update.message.text))
            admin_actions.magic(bot, update, 'admin_panel')

    except TelegramError as te:
        print(te.message)



