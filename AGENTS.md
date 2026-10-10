# Project Instructions

- 技術枠は Flask と Peewee。依頼なく別のWebフレームワークやORMへ変更・追加しない。
- 機能は小さく実装し、依頼範囲外の機能・大規模な構成変更を一度に追加しない。
- `SECRET_KEY`、パスワード、トークンなどの秘密情報をコードやGit管理対象のファイルへ書かない。環境変数を使う。
- ユーザー投稿画像はプロジェクト直下の `uploads/` に保存する。`static/` 配下には保存しない。
- 実装前に [docs/ai_context.md](docs/ai_context.md) と [docs/coding_rules.md](docs/coding_rules.md) を確認し、詳細な仕様・権限・実装規約に従う。
