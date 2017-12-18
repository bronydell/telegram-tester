from os import listdir
from pony import orm
from db import User, Results
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Bot, Update
from os.path import isfile, join
from actions import super_actions
import numpy as np

import random
import logging
import operator
import time
import json
import datetime


def get_tests():
    """Get list of available tests from folder /test_data/
    Returns
    -------
    list
        List of dictionaries with test data that was read from file
    """
    files = [f for f in listdir('tests_data') if isfile(join('tests_data', f))]
    result = []
    for file in files:
        with open('tests_data/' + file, encoding='UTF-8') as content_file:
            js = json.loads(content_file.read())
            js['id'] = content_file.name
            result.append(js)
    return result


def get_test(file):
    """Get dictionary with test info

    Parameters
    ----------
    file : str
        Full path to test file
    Returns
    -------
    dict
        List of dictionaries with test data that was read from file
    """
    with open(file, encoding='UTF-8') as ff:
        js = json.loads(ff.read())
        js['id'] = ff.name
        return js

def max_reward(test):
    """Calculate maximal reward

    Parameters
    ----------
    test : dict
        Test data presented by dict
    Returns
    -------
    int
        Max reward for this test
    """
    score = 0
    for q in test['questions']:
        score += q['reward']
    return score


@orm.db_session
def test_list(bot, update, is_update=False):
    """Show user list with tests

    Parameters
    ----------
    bot : Bot
        Bot provided by wrapper
    update : Update
        Update provided by wrapper
    is_update: bool
        Should we update message?
    Returns
    -------
    bool
        Is everything went fine?
    """
    user = User[update.effective_user.id]
    tests = get_tests()
    settings = super_actions.get_bot_settings(user.lang_file)
    test_ls = np.array([])
    for test in tests:
        test_ls = np.append(test_ls,
                            InlineKeyboardButton(text=test['title'],
                                                 callback_data='details_test {} {}'.format(test['id'], 'full')))
    if not is_update:
        bot.sendMessage(chat_id=user.id, text=settings['system_messages']['pick_test'],
                        reply_markup=InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1))))
        

    else:
        bot.editMessageText(chat_id=user.id, message_id=update.effective_message.message_id,
                            text=settings['system_messages']['pick_test'],
                            reply_markup=InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1))))
    return True


@orm.db_session
def completed_test_list(bot, update, is_update=False, n_cols=1):
    """Show user's completed list with tests

    Parameters
    ----------
    bot : Bot
        Bot provided by wrapper
    update : Update
        Update provided by wrapper
    is_update: bool
        Should we update message?
    n_cols: int
        Count of columns in buttons
    Returns
    -------
    bool
        Is everything went fine?
    """
    user = User[update.effective_user.id]
    settings = super_actions.get_bot_settings(user.lang_file)
    tests_wet = Results.select(lambda c: c.uid == user.id)
    test_ls = np.array([])
    if len(tests_wet) == 0:
        update.effective_message.reply_text(settings["system_messages"]["no_completed_tests"])
        super_actions.default_menu(bot, update)
        return True
    for test in tests_wet:
        test = get_test(test.test_id)
        test_ls = np.append(test_ls,
                            InlineKeyboardButton(text=test['title'],
                                                 callback_data='details_test {} {}'.format(test['id'], 'comp')))
    if not is_update:
        bot.sendMessage(chat_id=user.id, text=settings['system_messages']['comp_test_pick'],
                        reply_markup=InlineKeyboardMarkup(
                            [test_ls[i:i + n_cols] for i in range(0, len(test_ls), n_cols)]))
    else:
        bot.editMessageText(chat_id=user.id, message_id=update.effective_message.message_id,
                            text=settings['system_messages']['comp_test_pick'],
                            reply_markup=InlineKeyboardMarkup(
                                [test_ls[i:i + n_cols] for i in range(0, len(test_ls), n_cols)]))
    return True


@orm.db_session
def check_answer(bot, update, answer, question_num):
    """Check user's answer. This method writes results in database.

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        answer: int
            User's answer
        question_num: int
            Question number
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    test_action = user.action.split(' ')
    if len(test_action) < 2:
        return False
    logging.debug("User {} answered on question #{} from test {}".format(user.id, test_action[2], test_action[1]))
    test = get_test(test_action[1])
    question = int(test_action[2])
    if question != question_num:
        return False
    result = Results.get(uid=user.id, test_id=test['id'])
    score = result.results.get("score", 0)
    if test['questions'][question]['answer'] == test['questions'][question]['answers'][answer]:
        result.results['score'] = score + test['questions'][question]['reward']

    result.results['questions'][str(question)] = {
        "answer": test['questions'][question]['answers'][answer],
        "timer": time.time()
    }
    return True


@orm.db_session
def test_details(bot, update, filename, source='full'):
    """Show test details

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        filename: str
            Filename of test
        source: str
            From what list did me come from? For example, full means we came from list of all tests and
            comp means we came from completed tests
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    logging.debug("User {} asked for test {} details (source: {})".format(user.id, filename, source))
    settings = super_actions.get_bot_settings(user.lang_file)
    test = get_test(filename)
    # We need tags to get back to right menu
    tag = 'back_testlist'
    if source == 'comp':
        tag = 'back_comptestlist'

    keyboard = [
        [InlineKeyboardButton(text=settings['system_messages']['back_menu'],
                              callback_data='back_menu')],
        [InlineKeyboardButton(text=settings['system_messages']['back_to_tests'],
                              callback_data='{} {}'.format(tag, filename))]
    ]
    details = settings['system_messages']['test_details'].format(test['title'],
                                                                 test['author'], test['description'])
    if not Results.get(uid=user.id, test_id=test['id']) or test.get("repeatable", False):
        keyboard.insert(0, [InlineKeyboardButton(text=settings['system_messages']['run_test'],
                                                 callback_data='start_test ' + test['id'])])
    if Results.get(uid=user.id, test_id=test['id']):
        details = settings['system_messages']['test_details_results'].format(test['title'],
                                                                             test['author'],
                                                                             Results.get(uid=user.id,
                                                                                         test_id=test['id']).results[
                                                                                 'score'],
                                                                             max_reward(test),
                                                                             test['description'])

    bot.editMessageText(chat_id=user.id, message_id=update.effective_message.message_id,
                        text=details,
                        reply_markup=InlineKeyboardMarkup(keyboard))
    return True


@orm.db_session
def start_test(bot, update, test_file):
    """This method creates new record new database or overrides old. After this test begins!

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        test_file: str
            Filename of test
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    test = get_test(test_file)
    default_dict = {"score": 0, "timer": time.time(), "questions": {}}
    if Results.exists(uid=user.id, test_id=test['id']):
        logging.debug("User {} retaken test {}".format(user.id, test_file))
        Results.get(uid=user.id, test_id=test['id']).results = default_dict
    else:
        logging.debug("User {} started test {}".format(user.id, test_file))
        Results(uid=user.id, test_id=test['id'], results=default_dict)

    user.action = 'testing {} {}'.format(test['id'], -1)
    next_question(bot, update)
    return True


@orm.db_session
def next_question(bot, update, n_cols=1, finish = False):
    """This method edits message for next question of the test
    If this test is done it prints result and sends info to owner of the test

        Parameters
        ----------
        bot : Bot
            Bot provided by wrapper
        update : Update
            Update provided by wrapper
        n_cols: int
            Count of columns in buttons
        Returns
        -------
        bool
            Is everything went fine?
        """
    user = User[update.effective_user.id]
    settings = super_actions.get_bot_settings(user.lang_file)

    test_action = user.action.split(' ')
    filename = test_action[1]
    logging.debug("User {} asking for next question for test {}".format(user.id, filename))
    question = int(test_action[2]) + 1
    test = get_test(filename)
    options = []

    if question < len(test['questions']) and not finish:
        answers = test['questions'][question]['answers']
        mixed_answers = list(answers)
        random.shuffle(mixed_answers)
        for q in mixed_answers:
            options.append(InlineKeyboardButton(text=q,
                                                callback_data='answer {} {}'.format(answers.index(q), question)))
        markup = InlineKeyboardMarkup([options[i:i + n_cols] for i in range(0, len(options), n_cols)])

        if update.callback_query:
            if 'image' in test['questions'][question]:
                bot.sendPhoto(chat_id=user.id, photo=test['questions'][question]['image'],
                              caption=test['questions'][question]['question'],
                              reply_markup=markup)

            else:
                if 'image' in test['questions'][question - 1]:
                    bot.delete_message(chat_id=user.id, message_id=update.effective_message.message_id)
                    bot.sendMessage(user.id, text=test['questions'][question]['question'],
                                    reply_markup=markup)
                else:
                    bot.editMessageText(chat_id=user.id, message_id=update.effective_message.message_id,
                                        text=test['questions'][question]['question'],
                                        reply_markup=markup)
        else:
            if 'image' in test['questions'][question]:
                bot.sendPhoto(chat_id=user.id, photo=test['questions'][question]['image'],
                              caption=test['questions'][question]['question'],
                              reply_markup=markup)
            else:
                update.effective_message.reply_text(text=test['questions'][question]['question'],
                                                    reply_markup=markup)

        user.action = 'testing {} {}'.format(test['id'], question)
    else:
        result = Results.get(uid=user.id, test_id=test['id'])
        score = result.results['score']

        bot.editMessageText(chat_id=user.id, message_id=update.effective_message.message_id,
                            text=settings['system_messages']['test_solved'].format(score, max_reward(test)))
        if test.get("notify", None):
            details = ""
            logging.debug("User {} finished test {}. Notifying owner {}".format(user.id, filename, test.get("notify")))
            if test.get("detailed", None):
                details = settings['system_messages']['detailed_results'].format(
                    datetime.datetime.fromtimestamp(
                        int(result.results['timer'])).strftime('%Y-%m-%d %H:%M:%S'))
                for key, value in sorted(result.results['questions'].items(), key=operator.itemgetter(0)):
                    details += "{}. {} ({})\n".format(int(key) + 1, value['answer'],
                                                      datetime.datetime.fromtimestamp(
                                                          int(value['timer'])).strftime('%Y-%m-%d %H:%M:%S'))
            bot.sendMessage(chat_id=test.get("notify"),
                            text=settings['system_messages']['report_author'].format(
                                user.username,
                                user.name,
                                test['title'],
                                score,
                                max_reward(test)) + details)

        super_actions.default_menu(bot, update)
    return True
