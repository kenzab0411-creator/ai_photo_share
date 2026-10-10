from datetime import datetime
import os
from pathlib import Path

from cachelib import FileSystemCache
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_user,
    logout_user,
)
from flask_session import Session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from peewee import (
    AutoField,
    CharField,
    Check,
    DateTimeField,
    ForeignKeyField,
    IntegrityError,
    Model,
    SqliteDatabase,
)
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "instance" / "app.db"
database = SqliteDatabase(DATABASE_PATH, pragmas={"foreign_keys": 1})

load_dotenv(PROJECT_DIR / ".env")
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY を環境変数で設定してください。")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_TYPE="cachelib",
    SESSION_CACHELIB=FileSystemCache(str(PROJECT_DIR / "instance" / "flask_session")),
    SESSION_PERMANENT=False,
)
Session(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "この操作にはログインが必要です。"


class BaseModel(Model):
    class Meta:
        database = database


class User(UserMixin, BaseModel):
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


class RegistrationForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[DataRequired(), Length(min=1, max=80)],
    )
    password = PasswordField(
        "パスワード",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    password_confirmation = PasswordField(
        "パスワード（確認）",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("登録する")


class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_or_none(User.id == int(user_id))
    except ValueError:
        return None


def initialize_database():
    """Create the local SQLite database and the tables used in this app."""
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    database.connect(reuse_if_open=True)
    database.create_tables([User, Post])


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            User.create(
                username=form.username.data.strip(),
                password_hash=generate_password_hash(form.password.data),
            )
        except IntegrityError:
            form.username.errors.append("このユーザー名はすでに使われています。")
        else:
            flash("登録が完了しました。ログインしてください。")
            return redirect(url_for("login"))

    return render_template("auth/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_or_none(User.username == form.username.data.strip())
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=False)
            return redirect(url_for("index"))
        flash("ユーザー名またはパスワードが正しくありません。")

    return render_template("auth/login.html", form=form)


@app.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("ログアウトしました。")
    return redirect(url_for("index"))


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
