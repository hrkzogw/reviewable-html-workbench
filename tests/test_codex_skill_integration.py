from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Local fork (D2/D3): trigger sets narrowed to review-iteration intent /
# by-name invocation. These constants pin the FORK trigger contract; the
# removed generic triggers are pinned as absent below.
VISUAL_TRIGGER_EXAMPLES = [
    "レビュー可能なHTML",
    "レビューHTML",
    "コメントできるHTML",
    "reviewable HTML",
    "make this a reviewable HTML document",
]

VISUAL_REMOVED_TRIGGERS = [
    "html出力して",
    "HTMLにして",
    "HTMLで出して",
    "図示つきHTML",
    "render this as HTML",
    "turn this into HTML",
    "create an HTML preview",
    "generate a visual HTML report",
    "diagrammed HTML report",
]

REVIEWABLE_TRIGGER_EXAMPLES = [
    "レビュー可能な設計資料",
    "reviewable design doc",
    "レビュー終わったので確認して",
    "コメントを反映して",
    "create a reviewable design doc",
    "build a review-ready design document",
    "ingest review comments",
    "process review comments",
    "reply to review comments",
    "apply resolved comments",
]

REVIEWABLE_REMOVED_TRIGGERS = [
    "設計資料をHTMLで",
    "make a design doc in HTML",
]

PLAN_PREVIEW_TRIGGER_EXAMPLES = [
    "名指し",
]

PLAN_PREVIEW_REMOVED_TRIGGERS = [
    "planをグラフィカルに見たい",
    "planを図で確認したい",
    "この計画をHTMLでプレビューして",
    "計画をHTMLで確認したい",
    "graphical plan review",
    "proposed_planをプレビューして",
    "計画URLを入れて",
    "preview this plan as HTML",
    "show this plan visually",
    "graphical plan preview",
    "add a plan preview URL",
    "preview the proposed plan",
]


class CodexSkillIntegrationTest(unittest.TestCase):
    def test_skill_docs_pin_cli_workflows(self) -> None:
        visual = (ROOT / "skills/visual-html-renderer/SKILL.md").read_text(encoding="utf-8")
        reviewable = (ROOT / "skills/reviewable-design-doc/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("python3 -m scripts.html_review_workbench.cli build-model", visual)
        self.assertIn("python3 -m scripts.html_review_workbench.cli attach-image", visual)
        self.assertIn("python3 -m scripts.html_review_workbench.cli check-model", visual)
        self.assertIn("python3 -m scripts.html_review_workbench.cli render", visual)
        self.assertIn("python3 -m scripts.html_review_workbench.cli validate", visual)
        self.assertIn("python3 -m scripts.html_review_workbench.cli preview", visual)
        self.assertIn("renderer repo root", visual)
        self.assertIn("作業ディレクトリにして実行する", visual)
        self.assertIn("現在のチャットやworkspaceのcwdをrepo rootとして扱わない", visual)
        self.assertIn("代替HTMLを作らず", visual)
        self.assertIn("source-capture draft", visual)
        self.assertLess(visual.index("cli attach-image"), visual.index("cli check-model"))
        self.assertLess(visual.index("cli check-model"), visual.index("cli render"))
        self.assertLess(visual.index("cli attach-image"), visual.index("cli render"))
        self.assertLess(visual.index("cli render"), visual.index("cli validate"))
        self.assertLess(visual.index("cli validate"), visual.index("cli preview"))

        self.assertIn("python3 -m scripts.html_review_workbench.cli render", reviewable)
        self.assertIn("python3 -m scripts.html_review_workbench.cli attach-image", reviewable)
        self.assertIn("python3 -m scripts.html_review_workbench.cli check-model", reviewable)
        self.assertIn("python3 -m scripts.html_review_workbench.cli validate", reviewable)
        self.assertIn("python3 -m scripts.html_review_workbench.cli preview", reviewable)
        self.assertIn("python3 -m scripts.html_review_workbench.cli ingest-review", reviewable)
        self.assertIn("renderer repo root", reviewable)
        self.assertIn("作業ディレクトリにして実行する", reviewable)
        self.assertIn("現在のチャットやworkspaceのcwdをrepo rootとして扱わない", reviewable)
        self.assertIn("代替HTMLを作らず", reviewable)
        self.assertIn("source-capture draft", reviewable)
        self.assertLess(reviewable.index("cli attach-image"), reviewable.index("cli check-model"))
        self.assertLess(reviewable.index("cli check-model"), reviewable.index("cli render"))
        self.assertLess(reviewable.index("cli attach-image"), reviewable.index("cli render"))
        self.assertLess(reviewable.index("cli render"), reviewable.index("cli validate"))
        self.assertLess(reviewable.index("cli validate"), reviewable.index("cli preview"))
        self.assertLess(reviewable.index("cli preview"), reviewable.index("cli ingest-review"))

    def test_openai_metadata_matches_skill_docs(self) -> None:
        visual = _read_simple_yaml(ROOT / "skills/visual-html-renderer/agents/openai.yaml")
        reviewable = _read_simple_yaml(ROOT / "skills/reviewable-design-doc/agents/openai.yaml")
        plan_preview = _read_simple_yaml(ROOT / "skills/plan-preview/agents/openai.yaml")

        self.assertEqual(visual["entrypoint"], "python3 -m scripts.html_review_workbench.cli")
        self.assertEqual(visual["working_directory"], "plugin_root")
        self.assertEqual(visual["workflow"], ["attach-image", "check-model", "render", "validate", "preview"])
        for trigger in VISUAL_TRIGGER_EXAMPLES:
            self.assertIn(trigger, visual["trigger_examples"])

        self.assertEqual(reviewable["entrypoint"], "python3 -m scripts.html_review_workbench.cli")
        self.assertEqual(reviewable["working_directory"], "plugin_root")
        self.assertEqual(reviewable["workflow"], ["attach-image", "check-model", "render", "validate", "preview", "ingest-review"])
        for trigger in REVIEWABLE_TRIGGER_EXAMPLES:
            self.assertIn(trigger, reviewable["trigger_examples"])

        self.assertEqual(plan_preview["entrypoint"], "python3 -m scripts.html_review_workbench.cli")
        self.assertEqual(plan_preview["working_directory"], "plugin_root")
        self.assertEqual(plan_preview["workflow"], ["plan-preview"])
        # Local fork (D2): by-name invocation only; substring check because the
        # yaml carries a single descriptive entry rather than trigger phrases.
        joined_examples = " ".join(plan_preview["trigger_examples"])
        for trigger in PLAN_PREVIEW_TRIGGER_EXAMPLES:
            self.assertIn(trigger, joined_examples)

    def test_trigger_examples_are_documented_in_skills_and_readme(self) -> None:
        """Local fork (D2/D3): pin the narrowed trigger sets.

        The fork does not keep README trigger parity for narrowed triggers
        (README stays upstream); this test pins the SKILL.md contract only:
        the fork's positive triggers are present and the removed generic
        triggers stay absent in the description frontmatter.
        """
        skill_trigger_sets = [
            (
                ROOT / "skills/visual-html-renderer/SKILL.md",
                VISUAL_TRIGGER_EXAMPLES,
                VISUAL_REMOVED_TRIGGERS,
            ),
            (
                ROOT / "skills/reviewable-design-doc/SKILL.md",
                REVIEWABLE_TRIGGER_EXAMPLES,
                REVIEWABLE_REMOVED_TRIGGERS,
            ),
            (
                ROOT / "skills/plan-preview/SKILL.md",
                PLAN_PREVIEW_TRIGGER_EXAMPLES,
                PLAN_PREVIEW_REMOVED_TRIGGERS,
            ),
        ]
        for skill_path, triggers, removed in skill_trigger_sets:
            skill_text = skill_path.read_text(encoding="utf-8")
            description = skill_text.split("---", 2)[1]
            for trigger in triggers:
                self.assertIn(trigger, skill_text, f"{skill_path.name}: {trigger}")
            for trigger in removed:
                self.assertNotIn(trigger, description, f"{skill_path.name}: {trigger}")

    def test_skills_document_language_behavior(self) -> None:
        for skill in ["visual-html-renderer", "reviewable-design-doc", "plan-preview"]:
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("## 言語方針 / Language behavior", text)
            self.assertIn("Follow the language of the latest user request", text)

    def test_visual_skill_handles_natural_html_output_request_without_model_argument(self) -> None:
        visual = (ROOT / "skills/visual-html-renderer/SKILL.md").read_text(encoding="utf-8")

        # Local fork (D3): natural-language firing requires review-iteration intent.
        self.assertIn("レビュー可能なHTMLにして", visual)
        self.assertIn("レビュー往復意図のない一般の HTML 化依頼では発火させない", visual)
        self.assertIn("文書モデルが未指定の場合", visual)
        self.assertIn("HTML情報設計", visual)
        self.assertIn("HTML表現設計フェーズ", visual)
        self.assertIn("rendererブロック対応表", visual)
        self.assertIn("一時入力ファイルが必要な場合も `.md` は使わない", visual)
        self.assertIn("`build-model` は最終HTMLモデルを作るplannerではない", visual)
        self.assertIn("`section` / `text` / `table`", visual)
        self.assertIn("attach-image", visual)
        self.assertIn("render` → `validate` → `preview", visual)
        self.assertIn("返却JSONの `url`", visual)
        self.assertIn("Plan Mode 中の計画確認プレビュー", visual)
        self.assertIn("`plan-preview` を使う", visual)
        self.assertIn("Do not use this skill for Plan Mode proposal previews", visual)
        self.assertNotIn("--owner-pid $$", visual)
        self.assertNotIn("--owner-pid $PPID", visual)
        self.assertIn("標準では `--owner-pid` を渡さず", visual)
        self.assertIn("24時間アクセスが無い場合", visual)

    def test_reviewable_design_doc_builds_model_and_reports_preview_url(self) -> None:
        reviewable = (ROOT / "skills/reviewable-design-doc/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("最初から `document-model.json` を作る", reviewable)
        self.assertIn("`.md` を作らない", reviewable)
        self.assertIn("`.md` 原稿をHTMLへ変換する作業ではない", reviewable)
        self.assertIn("現行rendererに専用描画がない", reviewable)
        self.assertIn("source-capture draft", reviewable)
        self.assertIn("返却JSONの `url`", reviewable)
        self.assertNotIn("--owner-pid $$", reviewable)
        self.assertNotIn("--owner-pid $PPID", reviewable)
        self.assertIn("標準では `--owner-pid` を渡さず", reviewable)
        self.assertIn("24時間アクセスが無い場合", reviewable)

    def test_plan_preview_skill_guides_plan_mode_without_user_cli(self) -> None:
        """Local fork (D2): plan-preview fires only on explicit by-name requests."""
        plan_preview = (ROOT / "skills/plan-preview/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("名指しで依頼した場合のみ", plan_preview)
        self.assertIn("python3 -m scripts.html_review_workbench.cli plan-preview", plan_preview)
        self.assertIn("--mode local", plan_preview)
        self.assertIn("別端末からの閲覧を明示した場合に限り", plan_preview)
        self.assertIn("HTML_REVIEW_WORKBENCH_TAILSCALE_IP", plan_preview)
        self.assertIn("Plan preview: unavailable (<short reason>)", plan_preview)
        self.assertIn("ユーザーに CLI を実行させない", plan_preview)
        self.assertIn("hookを自動追加しない", plan_preview)
        self.assertIn("計画本文の全文を `source_text` にそのまま入れる", plan_preview)
        self.assertIn("要約・並べ替え・削除・言い換えは禁止", plan_preview)
        self.assertIn("受理されるトップレベル key は `title` / `source_text` / `diagrams` だけ", plan_preview)
        self.assertIn("HTMLは原文と同じ章構成・同じ内容で表示", plan_preview)
        self.assertIn("HTMLに追加されるのは、agentが `diagrams` で指定した図だけ", plan_preview)
        self.assertIn("The accepted top-level keys are only `title`, `source_text`, and `diagrams`", plan_preview)
        self.assertIn("The HTML preview must show the same section structure and same content as the original plan", plan_preview)
        self.assertNotIn("優先入口", plan_preview)
        self.assertNotIn("Tailscale / 外部公開", plan_preview)

    def test_same_fixture_keeps_artifact_structure_across_skill_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            visual_output = tmp_dir / "visual"
            reviewable_output = tmp_dir / "reviewable"
            model = ROOT / "tests/fixtures/minimal_document_model.json"

            _run_cli("render", "--model", str(model), "--output", str(visual_output))
            _run_cli("validate", "--root", str(visual_output))
            _run_cli("preview", "--root", str(visual_output), "--mode", "off")

            _run_cli("render", "--model", str(model), "--output", str(reviewable_output))
            _run_cli("validate", "--root", str(reviewable_output))
            _run_cli("preview", "--root", str(reviewable_output), "--mode", "off")
            (reviewable_output / "annotations").mkdir()
            shutil.copyfile(
                ROOT / "tests/fixtures/minimal_comments.json",
                reviewable_output / "annotations/comments.json",
            )
            _run_cli("ingest-review", "--root", str(reviewable_output))

            self.assertEqual(_artifact_paths(visual_output), _artifact_paths(reviewable_output, ignore_annotations=True))
            state = json.loads((reviewable_output / "annotations/review-cycle-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["total"], 1)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.html_review_workbench.cli", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def _artifact_paths(root: Path, *, ignore_annotations: bool = False) -> list[str]:
    paths: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        if ignore_annotations and relative.startswith("annotations/"):
            continue
        paths.append(relative)
    return sorted(paths)


def _read_simple_yaml(path: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    current_list: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_list:
            value = result[current_list]
            if not isinstance(value, list):
                raise AssertionError(f"expected list field: {current_list}")
            value.append(line[4:])
            continue
        current_list = None
        if line.endswith(":"):
            key = line[:-1]
            result[key] = []
            current_list = key
            continue
        key, value = line.split(": ", 1)
        result[key] = value
    return result


if __name__ == "__main__":
    unittest.main()
