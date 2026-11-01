"""Skill loader: short descriptions first, full playbook only when requested."""

import re
from pathlib import Path

SKILL_NAME = re.compile(r"^[a-z0-9-]+$")
DEFAULT_SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"


def _front_matter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def list_skills(skills_dir: Path = DEFAULT_SKILLS_DIR) -> list[dict[str, str]]:
    """Name and description of every skill folder that has a SKILL.md."""
    result = []
    for folder in sorted(Path(skills_dir).iterdir()):
        skill_file = folder / "SKILL.md"
        if folder.is_dir() and skill_file.is_file():
            meta = _front_matter(skill_file.read_text(encoding="utf-8"))
        result.append({"name": folder.name, "description": meta.get("description", "")})
    return result


def load_skill(name: str, skills_dir: Path = DEFAULT_SKILLS_DIR) -> str:
    """Full SKILL.md text. Refuses any name that is not a plain skill folder name."""
    if not SKILL_NAME.fullmatch(name):
        raise PermissionError(f"invalid skill name: {name!r}")
    skill_file = Path(skills_dir) / name / "SKILL.md"
    if not skill_file.is_file():
        raise FileNotFoundError(f"no such skill: {name}")
    return skill_file.read_text(encoding="utf-8")
