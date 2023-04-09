from mosiac import db

from sqlalchemy import TypeDecorator, Text
import json


class TupleType(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = tuple(json.loads(value))
        return value
# class TupleElement(db.Model):
#
#     id = db.Column(db.Integer, primary_key=True)
#     col1 = db.Column(db.Float)
#     col2 = db.Column(db.Float)
#     col3 = db.Column(db.Float)
#
#     def __init__(self, tup):
#         self.col1, self.col2, self.col3 = tup
#
#     @property
#     def as_tuple(self):
#         return self.col1, self.col2, self.col3

class Configuration(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    main_photo_dir = db.Column(db.String)
    tiles_photo_dir = db.Column(db.String)
    resized_tiles_photo_dir = db.Column(db.String)
    k = db.Column(db.Integer)
    tile_width = db.Column(db.Integer)
    tile_height = db.Column(db.Integer)
    output_photo_dir = db.Column(db.String)
    tiles_pickle = db.Column(db.PickleType)
    tree = db.Column(db.PickleType)
    tiles = db.Column(db.PickleType)


class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    tile_path = db.Column(db.String)
    resized_tile_path = db.Column(db.String)
    color = db.Column(TupleType)
    tile_pickle = db.Column(db.PickleType)



class MainImage(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    main_photo_path = db.Column(db.String)
    output_photo_path = db.Column(db.String)
    main_photo_width = db.Column(db.Float)
    main_photo_height = db.Column(db.Float)
    closest_paths = db.Column(db.PickleType)

