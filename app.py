from datetime import datetime
import os
from pathlib import Path
from uuid import uuid4

from cachelib import FileSystemCache
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_user,
    login_required,
    logout_user,
)
from flask_session import Session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileAllowed, FileField, FileRequired
from PIL import Image, UnidentifiedImageError
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
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from wtforms import PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "instance" / "app.db"
POST_UPLOAD_DIR = PROJECT_DIR / "uploads" / "posts"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
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
    MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE,
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


class PostForm(FlaskForm):
    image = FileField(
        "画像",
        validators=[
            FileRequired("画像を選択してください。"),
            FileAllowed(ALLOWED_IMAGE_EXTENSIONS, "PNG、JPG、JPEG、GIF画像のみ投稿できます。"),
        ],
    )
    caption = TextAreaField("キャプション（任意）", validators=[Length(max=200)])
    submit = SubmitField("投稿する")


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
    POST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def index():
    posts = (
        Post.select(Post, User)
        .join(User)
        .where(Post.visibility == "public")
        .order_by(Post.created_at.desc())
    )
    return render_template("index.html", posts=posts)


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


@app.route("/posts/new", methods=["GET", "POST"])
@login_required
def post_create():
    form = PostForm()
    if form.validate_on_submit():
        uploaded_file = form.image.data
        filename = secure_filename(uploaded_file.filename)
        extension = Path(filename).suffix.lower().lstrip(".")

        if not filename or extension not in ALLOWED_IMAGE_EXTENSIONS:
            form.image.errors.append("ファイル名または画像形式が正しくありません。")
        elif not is_valid_image(uploaded_file):
            form.image.errors.append("画像ファイルとして読み込めません。")
        else:
            POST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            stored_filename = f"{uuid4().hex}.{extension}"
            image_path = POST_UPLOAD_DIR / stored_filename
            try:
                uploaded_file.save(image_path)
                Post.create(
                    image_filename=stored_filename,
                    caption=form.caption.data.strip(),
                    user=current_user.id,
                )
            except Exception:
                image_path.unlink(missing_ok=True)
                raise

            flash("写真を投稿しました。")
            return redirect(url_for("index"))

    return render_template("posts/new.html", form=form)


@app.get("/uploads/posts/<filename>")
def uploaded_post_image(filename):
    return send_from_directory(POST_UPLOAD_DIR, filename)


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    flash("画像ファイルは5MB以下にしてください。")
    return redirect(url_for("post_create"))


def is_valid_image(uploaded_file):
    """Verify that the upload is an image, then reset its stream for saving."""
    try:
        Image.open(uploaded_file.stream).verify()
    except (UnidentifiedImageError, OSError):
        return False
    finally:
        uploaded_file.stream.seek(0)
    return True


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
