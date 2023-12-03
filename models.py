import atexit

from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.sqlite_ext import FTS5Model, SearchField
from peewee import CharField, ForeignKeyField, IntegerField, Model

from config import Config


db = SqliteQueueDatabase(Config.DB)

@atexit.register
def _stop_worker_threads():
    db.stop()

class Ticket(Model):
    id = IntegerField(primary_key=True)
    name = CharField(max_length=500)
    tag = CharField(max_length=10)
    
    class Meta:
        database = db

class TicketSearch(FTS5Model):
    name = SearchField()

    class Meta:
        database = db

class Image(Model):
    ticket = ForeignKeyField(Ticket)
    filename = CharField(max_length=100)
    file_id = CharField(max_length=100, null=True)
    
    class Meta:
        database = db
