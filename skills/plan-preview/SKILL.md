---
name: plan-preview
description: |
  ユーザーが「plan-preview」と名指しで依頼した場合のみ使用する skill。指定された計画本文を一時 HTML preview として表示する。名指しがない限り、プラン確認・プランのグラフィカル表示・「計画をHTMLで見たい」等の依頼でもこの skill を自動起動しない（プラン確認は利用環境の既定経路に従う）。Use this skill only when the user explicitly invokes it by the name "plan-preview". Never auto-trigger it for generic plan-review or plan-visualization requests; plan review follows the environment's default route. Triggers: ユーザーが「plan-preview」とスキル名を名指しした場合のみ / explicit invocation by the skill name "plan-preview" only。使用しない場面: 名指しのないプラン確認・プランレビュー一般、通常の最終HTML生成、レビュー可能な設計資料作成、コメント取り込み、恒久成果物の公開、外部アップロードが必要な図式化。Do not use for: any plan review that does not name this skill explicitly, final HTML artifacts, reviewable design docs, comment ingestion, permanent publication, or external-upload diagrams.
argument-hint: "[plan-preview-payload.json]"
strict_procedure: true
---

# plan-preview

## 役割

ユーザーが plan-preview を名指しで依頼したときに、指定された計画本文を一時 HTML preview として表示する。

このskillは利用者が手でコマンドを打つためのものではない。agentが `plan-preview` CLIを呼び、返却JSONの `url` を計画本文へ入れる。

この skill はプラン確認の既定経路ではない。名指しがない場合、プランの確認・レビュー・視覚化の依頼を本 skill へ route しない。

## Role

Render a plan text as a temporary HTML preview, only when the user has explicitly invoked this skill by name. The user should not run the CLI manually; the agent calls `plan-preview`, receives a session-scoped URL, and places that URL into the plan text. This skill is not the default route for plan review: without an explicit by-name request, do not route plan review or plan visualization here.

## Strict procedure profile

- Strictness: strict-procedure。正式な実装基準は計画本文であり、previewは判断補助として扱う。
- Hard gates: 外部サービス送信、shared state変更、永続ファイル出力、skill実行時にhookを動的に追加しない。
- Forcing function: `plan-preview` CLI、TTL付き一時ディレクトリ、`Plan preview: <url>` 行、失敗時の明示。
- Completion receipt: 名指しで起動された場合、計画本文に preview URL または `Plan preview: unavailable (<reason>)` を含める。

## 言語方針 / Language behavior

Follow the language of the latest user request for progress updates, preview labels, and the surrounding plan text. 日本語の依頼には日本語で、英語の依頼には英語で返す。`Plan preview: <url>` の固定ラベルは互換性のため英語のまま使ってよい。

## 発火条件

- ユーザーが「plan-preview」とスキル名を名指しして依頼した場合。これが唯一の発火条件。
- 名指しがない場合は、プランの確認・レビュー・図示・URL 追加の依頼であっても本 skill を使わない。

## Trigger Conditions

Use this skill only when the user invokes it by the name "plan-preview". That is the only trigger. Without the explicit name, do not use this skill for plan review, plan visualization, preview URLs, or any similar request.

## 使用しない場面

- 名指しのないプラン確認・プランレビュー一般（利用環境の既定経路に従う）。
- 最終成果物としてHTMLを生成する場合。これは `visual-html-renderer` を使う。
- レビュー可能な設計資料を作り、HTML上のコメントを取り込む場合。これは `reviewable-design-doc` を使う。
- planとは無関係な説明資料、恒久公開資料、Notion投稿、外部アップロードが必要な図式化。

## Do Not Use For

Do not use this skill for plan review that does not name it explicitly, final HTML artifacts, reviewable design documents, comment ingestion, unrelated explainers, permanent publications, Notion posts, or diagrams that require external uploads.

## 入力payload

agentは計画本文の全文を `source_text` にそのまま入れる。要約・並べ替え・削除・言い換えは禁止。
受理されるトップレベル key は `title` / `source_text` / `diagrams` だけ。`source_text` は必須。
`diagrams` は図が理解を助ける章だけに絞り、各図の `after_heading` は原文見出しのプレーンテキストと完全一致させる。

```json
{
  "title": "Plan Preview",
  "source_text": "計画本文 markdown 全文をそのまま",
  "diagrams": [
    {
      "after_heading": "実装手順",
      "title": "処理フロー",
      "mermaid": "flowchart TD\n  plan --> implementation"
    }
  ]
}
```

外部画像URL、外部asset、機密情報、未確定のsecret値はpayloadに入れない。

## Input Payload

Put the full markdown plan text into `source_text` exactly as-is. Do not summarize, reorder, delete, or rephrase it for preview generation. The accepted top-level keys are only `title`, `source_text`, and `diagrams`; `source_text` is required. Use `diagrams` only for sections where a diagram helps comprehension, and make each `after_heading` exactly match the plain-text heading in the source plan. Do not include external image URLs, external assets, secrets, or unconfirmed secret values.

## CLI手順

1. renderer repo root を作業ディレクトリにする。現在のチャットやworkspaceのcwdをrepo rootとして扱わない。
2. payloadを標準入力で渡して、次を実行する。preview は `local` mode（127.0.0.1）を既定にする。ユーザーが別端末からの閲覧を明示した場合に限り `auto` を使う。

```bash
python3 -m scripts.html_review_workbench.cli plan-preview --payload - --ttl 1800 --mode local
```

3. 成功したら返却JSONの `url` を計画本文に入れる。推奨表記:

```text
Plan preview: http://<bind-address>:<port>/index.html
```

ユーザーの明示依頼で `auto` を使う際、Codex sandbox内で Tailscale 検出に失敗する場合は、IPだけを先に取得して `HTML_REVIEW_WORKBENCH_TAILSCALE_IP=<tailscale-ip>` を渡してから `plan-preview --mode auto` を起動する。

4. 失敗しても計画提示を止めない。代わりに短い理由を入れる。

```text
Plan preview: unavailable (<short reason>)
```

5. `stop_command` はagent用の後片付け手段であり、通常はユーザーに実行させない。TTLで自動終了する。

## CLI Workflow

Run the CLI from the renderer repo root. Pass the plan payload through standard input with `python3 -m scripts.html_review_workbench.cli plan-preview --payload - --ttl 1800 --mode local`. Default to `local` (127.0.0.1); use `auto` only when the user explicitly asks to view from another device. On success, insert `Plan preview: <url>` into the plan text. On failure, do not block the plan; insert `Plan preview: unavailable (<short reason>)`. The returned `stop_command` is for agent cleanup and normally should not be handed to the user.

## 計画本文との関係

- 正式な実装基準は計画本文のテキスト。previewだけに存在する項目を作らない。
- preview URLは本文の冒頭または末尾ではなく、計画の確認に自然な位置へ置く。
- preview作成のために計画を短縮しない。HTMLは原文と同じ章構成・同じ内容で表示する。
- HTMLに追加されるのは、agentが `diagrams` で指定した図だけ。実装範囲や約束をpreviewだけに追加しない。
- previewの生成に失敗した場合でも、計画本文自体は成立させる。

## Relationship to the Plan Text

The authoritative implementation plan is the plan text, not the preview alone. Do not add implementation scope that exists only in the preview. Place the URL where it helps review the plan. Do not shorten the plan to make preview generation easier. The HTML preview must show the same section structure and same content as the original plan. The only added content is the diagrams explicitly provided by the agent in `diagrams`. If preview generation fails, still produce the plan with the unavailable reason.

## 禁止事項

- 名指しがないのに本 skill を起動しない。
- ユーザーに CLI を実行させない。
- hookを自動追加しない。
- `output/` やplugin cacheにpreview成果物を残さない。
- 外部アップロードを使わない。
- Preview Runtime の既定は `local`（127.0.0.1）。`auto`（Tailscale IPv4 優先）はユーザーが別端末からの閲覧を明示した場合に限る。
- preview URLを正式な実装基準として扱わない。

## Guards

Do not invoke this skill without an explicit by-name request. Do not ask the user to run the CLI. Do not auto-add hooks. Do not leave preview artifacts in `output/` or plugin cache. Do not use external uploads. Default to `local` (127.0.0.1); use `auto` (Tailscale-preferred) only when the user explicitly asks to view from another device. Do not treat the preview URL as the authoritative implementation plan.
