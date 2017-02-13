from os import listdir
from os.path import isfile, join
import json
import saver
from actions import super_actions
import numpy as np
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError
import random
import database.tests_db as testdb
from database import user_db as udb


def getTests():
    files = [f for f in listdir('tests_data') if isfile(join('tests_data', f))]
    result = []
    for file in files:
        with open('tests_data/' + file, encoding='UTF-8') as content_file:
            js = json.loads(content_file.read())
            js['id'] = content_file.name
            result.append(js)
    return result


def getTest(file):
    with open(file) as ff:
        js = json.loads(ff.read())
        js['id'] = ff.name
        return js


def maxReward(test):
    score = 0
    for q in test['questions']:
        score += q['reward']
    return score


def test_list(bot, update, last_one, is_update=False):
    if update.message:
        uid = update.message.from_user.id
    elif update.callback_query:
        uid = update.callback_query.from_user.id
    tests = getTests()
    settings = super_actions.getBotSettings(uid)
    test_ls = np.array([])

    for test in tests:
        test_ls = np.append(test_ls,
                            InlineKeyboardButton(text=test['title'],
                                                 callback_data='details_test {} {}'.format(test['id'], 'full')))
    if not is_update:
        bot.sendMessage(chat_id=uid, text=settings['system_messages']['pick_test'],
                        reply_markup=InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1))))
    else:
        bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                            text=settings['system_messages']['pick_test'],
                            reply_markup=InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1))))


def completedTestList(bot, update, is_update=False):
    if update.message:
        uid = update.message.from_user.id
    elif update.callback_query:
        uid = update.callback_query.from_user.id
    settings = super_actions.getBotSettings(uid)
    tests_wet = testdb.getAllTestsForUID(uid)
    test_ls = np.array([])
    for test_wet in tests_wet:
        test = getTest(test_wet)
        test_ls = np.append(test_ls,
                            InlineKeyboardButton(text=test['title'],
                                                 callback_data='details_test {} {}'.format(test['id'], 'comp')))
    if not is_update:
        bot.sendMessage(chat_id=uid, text=settings['system_messages']['comp_test_pick'],
                        reply_markup=InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1))))
    else:
        bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                            text=settings['system_messages']['comp_test_pick'],
                            reply_markup=InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1))))


def checkAnswer(bot, update, answer):
    uid = update.callback_query.from_user.id
    test_action = udb.getUserAction(uid, 'testing 0 0').split(' ')
    action = test_action[0]
    filename = test_action[1]
    question = int(test_action[2])
    score = saver.openPref(uid, 'test {}'.format(filename), 0)

    if getTest(filename)['questions'][question]['answer'] == getTest(filename)['questions'][question]['answers'][
        answer]:
        saver.savePref(uid, 'test {}'.format(filename), score + getTest(filename)['questions'][question]['reward'])
        print('Правильно')
    else:
        print('Нет')


def test_details(bot, update, filename, source='full'):
    if update.message:
        uid = update.message.from_user.id
    elif update.callback_query:
        uid = update.callback_query.from_user.id
    settings = super_actions.getBotSettings(uid)
    test = getTest(filename)
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
    if testdb.getScoreForUserByID(uid, test['id'], -1) == -1:
        keyboard.insert(0, [InlineKeyboardButton(text=settings['system_messages']['run_test'],
                                                 callback_data='start_test ' + test['id'])])
    else:
        details = settings['system_messages']['test_details_results'].format(test['title'],
                                                                                       test['author'],
                                                                                       testdb.getScoreForUserByID(uid,
                                                                                                                  test[
                                                                                                                      'id'],
                                                                                                                  -1),
                                                                                       maxReward(test),
                                                                                       test['description'])

    bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                        text=details,
                        reply_markup=InlineKeyboardMarkup(keyboard))


def start_test(bot, update, test_file):
    if update.message:
        uid = update.message.from_user.id
    elif update.callback_query:
        uid = update.callback_query.from_user.id
    test = getTest(test_file)
    saver.savePref(uid, 'test {}'.format(test['id']), 0)
    udb.setUserAction(uid, 'testing {} {}'.format(test['id'], -1))
    nextQuestion(bot, update)


def nextQuestion(bot, update):
    try:

        if update.message:
            uid = update.message.from_user.id
        elif update.callback_query:
            uid = update.callback_query.from_user.id
        settings = super_actions.getBotSettings(uid)
        test_action = udb.getUserAction(uid, 'testing 0 0').split(' ')
        filename = test_action[1]
        question = int(test_action[2]) + 1
        test = getTest(filename)
        test_ls = np.array([])

        if question < len(test['questions']):
            answers = test['questions'][question]['answers']
            mixed_answers = list(answers)
            random.shuffle(mixed_answers)
            for q in mixed_answers:
                test_ls = np.append(test_ls,
                                    InlineKeyboardButton(text=q, callback_data='answer {}'.format(answers.index(q))))
                print('answer {}'.format(answers.index(q)))
            markup = InlineKeyboardMarkup(np.reshape(test_ls, (-1, 1)))

            if update.callback_query:
                if 'image' in test['questions'][question]:
                    bot.sendPhoto(chat_id=uid, photo=open(test['questions'][question]['image'], 'rb'),
                                  caption=test['questions'][question]['question'],
                                  reply_markup=markup)

                else:
                    if 'image' in test['questions'][question - 1]:
                        bot.editMessageCaption(chat_id=uid, message_id=update.callback_query.message.message_id,
                                               caption=settings['system_messages']['question_solved'],
                                               reply_markup=None)
                        bot.sendMessage(uid, text=test['questions'][question]['question'],
                                        reply_markup=markup)
                    else:
                        bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                                            text=test['questions'][question]['question'],
                                            reply_markup=markup)
            else:
                if 'image' in test['questions'][question]:
                    bot.sendPhoto(chat_id=uid, photo=open(test['questions'][question]['image'], 'rb'),
                                  caption=test['questions'][question]['question'],
                                  reply_markup=markup)
                else:
                    bot.sendMessage(uid, text=test['questions'][question]['question'],
                                    reply_markup=markup)

            udb.setUserAction(uid, 'testing {} {}'.format(test['id'], question))
        else:
            score = saver.openPref(uid, 'test {}'.format(filename), 0)
            testdb.setTest(uid, score, test['id'])
            if 'notify' in test:
                test['author'] = test['author'][1:]
                if test['notify'] is True and udb.getID(test['author'], -1) != -1:
                    bot.sendMessage(chat_id=udb.getID(test['author'], None),
                    text=settings['system_messages']['report_author'].format(update.callback_query.from_user.username,
                                                                    test['title'], score, maxReward(test)))
            bot.editMessageText(chat_id=uid, message_id=update.callback_query.message.message_id,
                                text=settings['system_messages']['test_solved'].format(score, maxReward(test)))

            super_actions.menu(bot, update)

    except TelegramError as ex:
        print(ex.message)
