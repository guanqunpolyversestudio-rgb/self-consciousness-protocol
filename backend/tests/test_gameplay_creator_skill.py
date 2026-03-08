"""Gameplay creator skill smoke tests."""

import json
import re
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "gameplay-creator" / "scripts" / "create_gameplay_draft.py"
SKILL_PATH = PROJECT_ROOT / "gameplay-creator"


def test_gameplay_creator_skill_validates():
    content = (SKILL_PATH / "SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---\n")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match is not None
    frontmatter = match.group(1)
    assert "name: gameplay-creator" in frontmatter
    assert "description:" in frontmatter


def test_create_gameplay_draft_script(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "id": "visual-ritual",
                "name": "Visual Ritual",
                "summary": "A playful alignment loop with image prompts.",
                "loop": {
                    "cadence": "session",
                    "participants": "solo",
                    "phases": [
                        {"id": "check_in", "name": "Check In", "goal": "set the scene"},
                        {"id": "image", "name": "Image", "goal": "generate a symbolic image"},
                        {"id": "reflect", "name": "Reflect", "goal": "read the image back"},
                    ],
                },
                "interfaces": {"experience": {"type": "guided_experience"}},
                "required_tools": ["image.generate"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "drafts"
    result = subprocess.run(
        [
            "python3",
            str(SCRIPT_PATH),
            "--user-id",
            "draft_user",
            "--spec-file",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip())
    draft_path = Path(payload["path"])
    assert draft_path.exists()
    content = draft_path.read_text(encoding="utf-8")
    assert '"required_tools": [' in content
    assert "image.generate" in content
