from mongoengine import Document, FloatField, StringField, IntField


class Tick(Document):
    close_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()
    open_price = FloatField()
    name = StringField()
    time = StringField(unique_with='tick_unit')
    tick_unit = IntField()


class Minute(Document):
    close_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()
    open_price = FloatField()
    name = StringField()
    time = StringField(unique_with='minute_unit')
    minute_unit = IntField()
