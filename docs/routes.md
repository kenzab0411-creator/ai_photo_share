# ルーティング設計

## 方針

- Flask のビュー関数は、画面または操作ごとに分ける。
- 表示用のリクエストは `GET`、データ作成・更新・削除は `POST` を使う。
- 投稿IDは URL の `<int:post_id>` で受け取る。
- ログインが必要なルートでは、未ログインなら `/login` へ移動させる。
- 他人の投稿の編集・削除、および他人の非公開投稿の閲覧は許可しない。

## ルート一覧

| URL | HTTPメソッド | ビュー関数名（例） | テンプレート | ログイン | 処理 |
| --- | --- | --- | --- | --- | --- |
| `/` | `GET` | `post_index` | `posts/index.html` | 不要 | 公開投稿を新しい順で表示する。ログイン中で `visibility=private` の場合は、自分の非公開投稿だけを表示する。 |
| `/register` | `GET` | `register` | `auth/register.html` | 不要 | ユーザー登録フォームを表示する。 |
| `/register` | `POST` | `register` | `auth/register.html` | 不要 | 入力を検証し、ユーザーを登録する。成功時は `/login` へ移動する。 |
| `/login` | `GET` | `login` | `auth/login.html` | 不要 | ログインフォームを表示する。 |
| `/login` | `POST` | `login` | `auth/login.html` | 不要 | 認証に成功したらセッションへユーザーIDを保存し、`/` へ移動する。 |
| `/logout` | `POST` | `logout` | なし | 必要 | セッションを削除し、`/` へ移動する。 |
| `/posts/new` | `GET` | `post_create` | `posts/new.html` | 必要 | 投稿作成フォームを表示する。 |
| `/posts/new` | `POST` | `post_create` | `posts/new.html` | 必要 | 画像を保存し、投稿を作成する。成功時は `/` へ移動する。 |
| `/posts/<int:post_id>` | `GET` | `post_detail` | `posts/detail.html` | 不要（非公開は本人のみ） | 投稿を表示する。非公開投稿は投稿者本人以外には表示しない。 |
| `/posts/<int:post_id>/edit` | `GET` | `post_edit` | `posts/edit.html` | 必要（投稿者本人） | 投稿編集フォームを表示する。 |
| `/posts/<int:post_id>/edit` | `POST` | `post_edit` | `posts/edit.html` | 必要（投稿者本人） | キャプションと公開範囲を更新する。成功時は投稿詳細へ移動する。 |
| `/posts/<int:post_id>/delete` | `GET` | `post_delete` | `posts/delete_confirm.html` | 必要（投稿者本人） | 削除確認画面を表示する。 |
| `/posts/<int:post_id>/delete` | `POST` | `post_delete` | なし | 必要（投稿者本人） | 投稿データと画像ファイルを削除し、`/` へ移動する。 |

## クエリパラメータ

投稿一覧でログイン中のユーザーがタブを切り替えるため、次を使用する。

| URL例 | 意味 | 利用条件 |
| --- | --- | --- |
| `/?visibility=public` | 公開投稿を表示する。省略時も公開投稿を表示する。 | 誰でも利用可能 |
| `/?visibility=private` | ログイン中の本人が作成した非公開投稿を表示する。 | ログインが必要 |

未ログインで `/?visibility=private` を開いた場合は、ログイン画面へ移動する。

## リダイレクトとエラー時の扱い

| 状況 | 動作 |
| --- | --- |
| 未ログインで投稿作成・編集・削除を開く | `/login` へリダイレクトする。 |
| 未ログインで非公開タブを開く | `/login` へリダイレクトする。 |
| 他人の非公開投稿詳細を開く | `404 Not Found` を返す。存在の有無を知らせないため。 |
| 他人の投稿の編集・削除URLを開く | `403 Forbidden` を返す。 |
| 存在しない投稿IDを開く | `404 Not Found` を返す。 |
| 登録・ログイン・投稿フォームの入力エラー | 同じフォーム画面を再表示し、エラーメッセージを表示する。 |

## 実装時の補足

- `GET /logout` にしない。リンクではなくフォームの `POST` でログアウトする。
- 投稿作成フォームでは画像を送信するため、フォームに `enctype="multipart/form-data"` を設定する。
- 編集・削除の各ビュー関数では、投稿を取得した直後に「現在ログイン中のユーザーが投稿者か」を確認する。
- いいね・コメントのルートは、この版では作成しない。機能追加時に `/posts/<int:post_id>/likes` と `/posts/<int:post_id>/comments` などを別途設計する。
