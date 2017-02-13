import database.user_db as udb
import database.admin_db as admindb
import database.tests_db as testdb
import os
import sqlite3
import sys
import json
import shelve

shelve_name = "users_db"

def savePref(user, key, value):
    d = shelve.open(shelve_name)
    d[str(user) + '.' + str(key)] = value
    d.close()


def openPref(user, key, default):
    d = shelve.open(shelve_name)
    if (str(user) + '.' + str(key)) in d:
        return d[str(user) + '.' + str(key)]
    else:
        return default

def getPricing():
    with open('subscriptions.json', encoding='UTF-8') as data_file:
        data = json.load(data_file)
    return data

def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def isAdmin(id):
    if id in admindb.getAllAdmins():
        return True
    return False


def initDataBase():
    global filename
    filename = "data"
    conn = sqlite3.connect(filename + ".db")
    c = conn.cursor()

    # Create tables
    udb.initDB(filename)
    admindb.initDB(filename)
    testdb.initDB(filename)
    conn.commit()
    conn.close()
