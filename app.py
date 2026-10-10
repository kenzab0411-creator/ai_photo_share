from datetime import datetime
from pathlib import Path

from flask import Flask
from peewee import (
    AutoField,
    CharField,
    Check,
    DateTimeField,
    ForeignKeyField,
    Model,
    SqliteDatabase,
)


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "instance" / "app.db"
database = SqliteDatabase(DATABASE_PATH, pragmas={"foreign_keys": 1})

app = Flask(__name__)


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    id = AutoField()
    username = CharField(unique=True)
    password_hash = CharField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "users"


class Post(BaseModel):
    id = AutoField()
    image_filename = CharField(unique=True)
    caption = CharField(max_length=200, default="")
    visibility = CharField(
        default="public",
        constraints=[Check("visibility IN ('public', 'private')")],
    )
    user = ForeignKeyField(User, backref="posts")
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "posts"


def initialize_database():
    """Create the local SQLite database and the tables used in this minimal app."""
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    database.connect(reuse_if_open=True)
    database.create_tables([User, Post])


@app.get("/")
def index():
    return "写真共有アプリ"


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
