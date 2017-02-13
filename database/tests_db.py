import sqlite3
# Database name
filename = "data"

tests_table_name = "tests"


tests_generate = "create table if not exists " + tests_table_name + \
                 " (id INTEGER PRIMARY KEY, uid integer, test_id text, score integer)"

test_get_all_users = "SELECT uid FROM " + tests_table_name + " WHERE test_id = ?"

get_score_by_test_and_id = "SELECT score FROM " + tests_table_name + " WHERE uid = ? and test_id = ?"

get_tests_by_uid = "SELECT test_id FROM " + tests_table_name + " WHERE uid = ?"

get_score_by_testid = "SELECT * FROM " + tests_table_name + " WHERE test_id = ?"

def getAllTesters(test_id):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(test_get_all_users, [test_id])
    wet_data = c.fetchall()
    users = []
    for user in wet_data:
        users += user
    conn.commit()
    conn.close()
    return users

def getAllTestsForUID(uid):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_tests_by_uid, [uid])
    wet_data = c.fetchall()
    tests = []
    for test in wet_data:
        tests += test
    conn.commit()
    conn.close()
    return tests

def getScoreByTest(test_id):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_score_by_testid, [test_id])
    wet_data = c.fetchall()
    print(wet_data)

def getScoreForUserByID(uid, test_id, default):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_score_by_test_and_id, [uid, test_id])
    wet_data = c.fetchone()
    if wet_data is None:
        return default
    else:
        return wet_data[0]

def setTest(uid, score ,test_id):
    if getScoreForUserByID(uid, test_id, -1) == -1:
        conn = sqlite3.connect(filename + '.db')
        c = conn.cursor()
        # Insert or replace action for user
        test_update = "update " + tests_table_name + " SET uid = ?, test_id = ?, score = ? WHERE uid = ? and test_id=?;"
        c.execute(test_update, [uid, test_id, score, uid, test_id])
        # If not succeed
        test_update = "insert or ignore INTO " + tests_table_name + "(uid, score, test_id) VALUES (?, ?, ?);"
        c.execute(test_update, [uid, score, test_id])
        conn.commit()
        conn.close()

def initDB(file):
    global filename
    filename = file
    conn = sqlite3.connect(file + ".db")
    c = conn.cursor()
    c.execute(tests_generate)
    conn.commit()
    conn.close()
