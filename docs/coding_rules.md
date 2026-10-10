# コーディング規約

## 技術と構成

- FlaskとPeeweeを使用する。Flask-SQLAlchemy、Djangoなどの別ORM・別フレームワークは追加しない。
- 初回版は `app.py` を中心に実装し、不要な抽象化やBlueprintは導入しない。
- テンプレートは `templates/auth/` と `templates/posts/` に分類する。
- `static/` はCSS・JavaScript用、ユーザー投稿画像はプロジェクト直下の `uploads/` に保存する。
- `uploads/` は公開用の静的フォルダではないため、画像表示は `/uploads/<filename>` の専用GETルートで行う。URLに渡すファイル名はDBに保存した名前だけを使う。
- SQLite DBは `instance/app.db` に置く。

## データベース

- モデル名は単数形の `User`、`Post`、`Like`、`Comment`、テーブル名は複数形の `users`、`posts`、`likes`、`comments` とする。
- `Post.user`、`Like.user`、`Like.post`、`Comment.user`、`Comment.post` はPeeweeの `ForeignKeyField` を使う。
- `User.username` と `Post.image_filename` は一意にする。
- `Like` は `(user, post)` の複合ユニーク制約を必ず設定する。
- `Post.visibility` は `public` と `private` のみを許可する。
- 日時は作成時に設定し、`Post.updated_at` は編集時に更新する。
- SQLiteの外部キー制約を有効にする。

## 認証・権限

- Flask-Loginで現在のユーザーを取得し、投稿作成・編集・削除、いいね、コメントにはログイン必須の制御を付ける。
- Flask-SessionとCacheLibでサーバー側セッションを使う。セッションはブラウザ終了時に終了する。
- 「投稿者本人か」「投稿が公開か」を、URLを受け取る各ビュー関数内で必ず確認する。
- 他人の非公開投稿は404、他人の投稿の編集・削除は403とする。
- パスワードはWerkzeugのハッシュ化・照合機能を使い、平文を保存・ログ出力しない。

## フォームと入力検証

- Flask-WTFを使い、すべてのPOSTフォームでCSRF保護を有効にする。
- 画面での検証だけに依存せず、ビュー関数でも公開範囲・権限・ファイルを検証する。
- キャプションは任意で最大200文字、コメントは必須かつ空白だけを許可しない。
- ログアウトと削除はGETで実行しない。確認画面はGET、実際の変更はPOSTにする。

## 画像の扱い

- アップロードフォームには `enctype="multipart/form-data"` を設定する。
- 拡張子とMIMEタイプだけを信用せず、PillowでJPEG・PNG・WebPとして開けるか確認する。
- 受け付ける画像は最大5MB。保存前にサイズを確認する。
- 元のファイル名は保存名に使わない。ランダムUUID等で一意なファイル名を作る。
- 投稿レコード作成に失敗した場合は、保存済みの不要画像を可能な限り削除する。
- 投稿削除時は、投稿レコードと対応する `uploads/` の画像を両方削除する。

## 設定・エラー処理

- `SECRET_KEY`などの秘密情報は環境変数から読む。開発用`.env`はGit管理しない。
- DBパス、`uploads/`パス、最大アップロードサイズ、許可拡張子は設定値としてまとめる。
- 利用者の入力エラーは同じ画面に分かりやすく表示する。
- 想定外の例外内容や秘密情報を利用者画面に表示しない。
