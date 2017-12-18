from pony import orm

db = orm.Database()


class User(db.Entity):
    id = orm.PrimaryKey(int)
    username = orm.Optional(str)
    name = orm.Required(str)
    action = orm.Optional(str)
    lang_file = orm.Optional(str)
    info = orm.Optional(orm.Json)


class Admin(db.Entity):
    id = orm.PrimaryKey(int, auto=True)


class Results(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    uid = orm.Required(int)
    test_id = orm.Required(str)
    results = orm.Required(orm.Json)


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
