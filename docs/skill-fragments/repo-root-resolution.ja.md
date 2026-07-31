CLI実行前に、この `SKILL.md` の配置から renderer repo root を決める。
`{{skill_path}}` の2階層上が renderer repo root であり、
そこに `scripts/html_review_workbench/cli.py` が存在することを確認する。
すべての `python3 -m scripts.html_review_workbench.cli ...` は renderer repo root を
作業ディレクトリにして実行する。現在のチャットやworkspaceのcwdをrepo rootとして扱わない。
cwdに `scripts/html_review_workbench/cli.py` が無い場合は、代替HTMLを作らず、
renderer repo rootへ移動してCLIを実行する。

出力はこの規約の対象にしない。`render` の `--output`、`preview` / `validate` /
`ingest-review` 等の `--root`、および bundle の置き場所は、renderer repo root 配下にも
plugin cache 配下にも置かず、運用側で定めた永続 output root（このリポジトリの外）への
絶対パスで指定する。renderer repo root が plugin cache 内に解決される場合
（インストール配備）、cache への書き込みは一切行わない。
