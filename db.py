from aiopeewee import PeeweeASGIPlugin
import peewee as pw
import config

db = PeeweeASGIPlugin(url='sqlite+async:///db.sqlite')


@db.register
class User(pw.Model):
    id = pw.IntegerField(unique=True, primary_key=True)  # id пользователя
    admin = pw.BooleanField(default=False)


db.create_tables()
