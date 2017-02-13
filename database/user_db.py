import sqlite3
# Database name
filename = "data"

# User table name
user_table_name = "users"

# User table generate request
users_generate = "create table if not exists " + user_table_name + \
                 " (id integer PRIMARY KEY, username text, action text)"

# Get ALL users ids
get_everything = "SELECT id FROM " + user_table_name

# Get user action
get_action = "SELECT action FROM " + user_table_name + " WHERE id = ?"


# Get users username
get_username = "SELECT username FROM " + user_table_name + " WHERE id = ?"

# Get users id
get_id = "SELECT id FROM " + user_table_name + " WHERE username = ?"




def getID(username, default):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_id, [username])
    id = c.fetchone()
    conn.commit()
    conn.close()
    if id is None:
        return default
    else:
        return id[0]

def getAllUsers():
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_everything)
    wet_data = c.fetchall()
    users = []
    for user in wet_data:
        users += user
    conn.commit()
    conn.close()
    return users

def setUserUsername(id, username):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    # Insert or replace action for user
    username_update = "update " + user_table_name + " SET id = ?, username = ? WHERE id = ?;"
    c.execute(username_update, [id, username, id])
    # If not succeed
    username_update = "insert or ignore INTO " + user_table_name + "(id, username) VALUES (?, ?);"
    c.execute(username_update, [id, username])
    conn.commit()
    conn.close()


def getUsernamebyID(id, default):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_username, [id])
    username = c.fetchone()
    conn.commit()
    conn.close()
    if username is None:
        return default
    else:
        return username[0]

def getActionbyID(id):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_action, [id])
    action = c.fetchone()
    conn.commit()
    conn.close()
    return action



def initDB(file):
    global filename
    filename = file
    conn = sqlite3.connect(file + ".db")
    c = conn.cursor()
    c.execute(users_generate)
    conn.commit()
    conn.close()

def getUserAction(id, default):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    c.execute(get_action, [id])
    data = c.fetchone()[0]
    conn.commit()
    conn.close()
    if data:
        return data
    return default

def setUserAction(id, action):
    conn = sqlite3.connect(filename + '.db')
    c = conn.cursor()
    # Insert or replace action for user
    action_update = "update " + user_table_name + " SET id = ?, action = ? WHERE id = ?;"
    c.execute(action_update, [id, action, id])
    # If not succeed
    action_update = "insert or ignore INTO " + user_table_name + "(id, action) VALUES (?, ?);"
    c.execute(action_update, [id, action])
    conn.commit()
    conn.close()