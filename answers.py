from db import User, Admin
from pony import orm
import logging
from actions import super_actions, admin_actions
from actions import test_actions as tests
import telegram
from telegram import TelegramError


def perform(bot, update, action):
    if action == 'menu':
        super_actions.default_menu(bot, update)
    elif action == 'send_msg_all':
        admin_actions.admin_menu(bot, update, 'send_msg_all')
    elif action == 'edit_prefs':
        admin_actions.edit_preference(bot, update)
    elif action == 'add_admin':
        admin_actions.admin_menu(bot, update, 'add_admin')
    elif action == 'del_admin':
        admin_actions.admin_menu(bot, update, 'del_admin')
    elif action == 'admin':
        admin_actions.admin_menu(bot, update, 'admin_panel')
    elif action == 'completed_tests':
        tests.completed_test_list(bot, update)
    elif action == 'change_language':
        super_actions.get_languages(bot, update)
    elif action == 'test':
        tests.test_list(bot, update, False)


@orm.db_session
def click(bot, update):
    try:
        uid = update.effective_user.id
        data = update.callback_query.data
        user = User[uid]
        logging.debug("User {} clicked on button with data {}".format(uid, data))

        if data.startswith('answer'):
            answ = data.split(' ')
            if tests.check_answer(bot, update, int(answ[1]), int(answ[2])):
                tests.next_question(bot, update)
        elif data.startswith('back_menu'):
            bot.delete_message(chat_id=uid, message_id=update.callback_query.message.message_id)
            super_actions.default_menu(bot, update)

        elif data.startswith('back_testlist'):
            # filename = data.split(' ')[1]
            tests.test_list(bot, update, is_update=True)

        elif data.startswith('back_comptestlist'):
            # filename = data.split(' ')[1]
            tests.completed_test_list(bot, update, is_update=True)

        elif data.startswith('details_test'):
            splited = data.split(' ')
            filename = splited[1]
            source = splited[2]

            tests.test_details(bot, update, filename, source=source)

        elif data.startswith('start_test'):
            filename = data.split(' ')[1]
            # bot.delete_message(chat_id=uid, message_id=update.callback_query.message.message_id)
            tests.start_test(bot, update, filename)
    except TelegramError as te:
        logging.error(te.message)
        pass


@orm.db_session
def def_menu(bot, update):
    uid = update.effective_user.id
    if not User.exists(id=uid):
        user = User(id=uid,
                    action=super_actions.get_bot_settings("bot.json")['default_menu'],
                    name=update.effective_user.first_name + " "+
                    update.effective_user.last_name if update.effective_user.last_name else "",
                    username=update.effective_user.username if update.effective_user.username else "",
                    lang_file="bot.json",
                    info={})
    else:
        user = User[uid]
    if user.action.startswith('testing'):
        try:
            tests.next_question(bot, update, finish=True)
        except Exception as ex:
            print(ex)
            super_actions.default_menu(bot, update)

        return True
    else:
        super_actions.default_menu(bot, update)
        return True


# Response to plain messages
@orm.db_session
def answer(bot, update):
    uid = update.effective_user.id
    logging.debug("User {} sent message".format(uid))
    # Get or create user
    if not User.exists(id=uid):
        user = User(id=uid,
                    action=super_actions.get_bot_settings("bot.json")['default_menu'],
                    name=update.effective_user.first_name +
                    update.effective_user.last_name if update.effective_user.last_name else "",
                    username=update.effective_user.username if update.effective_user.username else "",
                    lang_file="bot.json",
                    info={})
    else:
        user = User[uid]
    # Update user's info like name or username
    user.username = update.effective_user.username if update.effective_user.username else ""
    user.name = update.effective_user.first_name + " " + update.effective_user.last_name \
        if update.effective_user.last_name else ""
    settings = super_actions.get_bot_settings(user.lang_file)
    act = user.action

    if act in settings:
        for option in settings[act]['keyboard']:
            if option['text'] == update.message.text:
                if option.get('action'):
                    perform(bot, update, option['action'])
                if option.get('message'):
                    update.effective_message.reply_text(option.get('message'))
                return None
    elif act == 'pick_language':
        if not super_actions.set_locale(user, update.message.text):
            update.effective_message.reply_text("Language doesn't exist")
        else:
            super_actions.default_menu(bot, update)
    elif act == 'send_msg_all':
        admin_actions.send_to_everyone(bot, update, update.message.text)
        admin_actions.admin_menu(bot, update, 'admin_panel')
    elif act == 'edit_prefs':
        admin_actions.replace_settings(bot, update, 'bot')
    elif act == 'add_admin':
        Admin(id=int(update.message.text))
        admin_actions.admin_menu(bot, update, 'admin_panel')
    elif act == 'del_admin':
        if Admin.exists(id=int(update.message.text)):
            Admin.get(id=int(update.message.text)).delete()
        admin_actions.admin_menu(bot, update, 'admin_panel')
    elif act.startswith('testing'):
            answ = user.action.split(' ')
            test = tests.get_test(answ[1])
            if test.get('custom', False):
                if tests.check_answer(bot, update, test['id'], int(answ[2]), custom_text=update.effective_message.text):
                    tests.next_question(bot, update)

