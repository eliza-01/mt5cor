#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tools/dump/main.py

"""
Собирает файлы проекта в один txt, разделяя блоки путями исходных файлов.
Разделитель: строка вида `# src/index.ts`

Корень проекта:
1) --root
2) PROJECT_ROOT (env)
3) (ПО УМОЛЧАНИЮ) ищем ближайший родительский каталог с `pyproject.toml`
   относительно расположения этого скрипта.

ВАЖНО:
- файл дампа создаётся рядом со скриптом (по умолчанию project_bundle.txt).
- если --out относительный — он считается относительно директории скрипта.
- выходной файл дампа НИКОГДА не включается в дамп (чтобы не включать сам себя).
- .env (и любые .env.* кроме .env.example) НЕ включаются по умолчанию, чтобы не сливать секреты.

ПРАВИЛА include/ignore:
- INCLUDE_DIRS: список директорий (относительно корня проекта). Каждая отдаёт ВСЕ файлы рекурсивно.
- INCLUDE_FILES: список файлов (относительно корня проекта), которые нужно добавить явно.
- IGNORE_DIRS: список директорий (относительно корня проекта). Игнор работает по ОТНОСИТЕЛЬНОМУ ПУТИ, не по имени.
  Пример: IGNORE_DIRS = {"dist"} игнорирует <root>/dist, но НЕ игнорирует <root>/src/dist.
- IGNORE_FILES: можно задавать как имена (например, "Thumbs.db"), так и относительные пути.
- Игноры в приоритете: если что-то попало в IGNORE_* — оно не попадёт в дамп даже если включено через INCLUDE_*.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Set, List, Optional


# =========================
# ====== Х Е Д Е Р ========
# =========================

# True — собрать все файлы из каталогов INCLUDE_DIRS (плюс INCLUDE_FILES)
# False — собрать только файлы из INCLUDE_FILES
ALL_FILES: bool = True

# Директории (относительно корня проекта), из которых собираем ВСЁ рекурсивно.
INCLUDE_DIRS: List[str] = [
    # "src",
    # "data",
    "src/app/ui_relative_compare",
    # "fxrelval_mt5/src",
    # "src/app/ui_relative_compare",
]

# Файлы (относительно корня проекта), которые добавляем явно.
INCLUDE_FILES: List[str] = [
    ".env.example",
    ".gitignore",
    "patch.py",
    "pyproject.toml",
    "README.md",
    "requirements.txt",

    "fxrelval_mt5/.env.example",
    "fxrelval_mt5/.gitignore",
    "fxrelval_mt5/pyproject.toml",
    "fxrelval_mt5/README.md",
    "fxrelval_mt5/requirements.txt",
]

# Директории, которые НИКОГДА не кладём в дамп (по относительному пути от корня проекта).
# ВАЖНО: это именно относительные пути, а не "имена где угодно".
IGNORE_DIRS: Set[str] = {
    ".git",
    ".idea",
    ".vscode",

    # python cache / build
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".eggs",
    "*.egg-info",

    # build/artifacts
    "dist",
    "build",
    "out",
    "coverage",
    "htmlcov",

    # окружения/локальные данные
    "venv",
    ".venv",
    "env",
    "logs",

    "tools",
}

# Файлы, которые НИКОГДА не кладём в дамп.
# Можно указывать:
# - просто имя: "Thumbs.db" (игнорируется везде)
# - относительный путь: "tools/dump/project_bundle.txt" (игнорируется только этот файл)
IGNORE_FILES: Set[str] = {
    ".DS_Store",
    "Thumbs.db",

    # output bundles
    "project_bundle.txt",

    # python artifacts
    ".coverage",

    # secrets
    ".env",
}

# Разрешённые расширения (пустое множество => разрешены все)
ALLOWED_EXTS: Set[str] = {
    # docs/config
    ".md",
    ".txt",
    ".toml",
    ".ini",
    ".cfg",
    ".yml",
    ".yaml",

    # python
    ".py",

    # data
    # ".csv",

    # misc
    ".sh",
    ".bat",
    ".ps1",
}

# Разрешённые имена файлов без расширений / dotfiles (например .gitignore)
ALLOWED_NAMES: Set[str] = {
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    "Dockerfile",
    "LICENSE",
    "Makefile",
}

# Ограничение на размер одного файла (байты), 0 = без ограничения
MAX_FILE_SIZE_BYTES: int = 0

# Имя выходного файла по умолчанию (создаётся РЯДОМ СО СКРИПТОМ)
DEFAULT_OUTPUT: str = "project_bundle.txt"


# =========================
# ====== Р Е А Л И З ======
# =========================

def normalize_rel_posix(p: str) -> str:
    """Нормализуем относительный путь под posix и убираем лишнее."""
    p = p.strip().replace("\\", "/")
    if p == "":
        return ""
    return Path(p).as_posix().lstrip("/")


def find_project_root_by_markers(start: Path) -> Optional[Path]:
    """
    Ищем вверх от start ближайший каталог с маркерами проекта.
    Для Python — `pyproject.toml` (основной маркер).
    """
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent

    for parent in [cur, *cur.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    return None


def script_based_project_root() -> Path:
    """
    По умолчанию считаем корнем ближайшую директорию с pyproject.toml
    относительно расположения скрипта.
    """
    here = Path(__file__).resolve()
    found = find_project_root_by_markers(here)
    if found is not None:
        return found
    # fallback: каталог скрипта (на всякий)
    return here.parent


def detect_project_root(cli_root: Optional[str]) -> Path:
    if cli_root:
        return Path(cli_root).expanduser().resolve()

    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    return script_based_project_root()


def is_ignored_dir_rel(rel_dir_posix: str) -> bool:
    """
    rel_dir_posix — относительный путь директории от корня проекта, posix.
    Игнорируем, если:
    - rel == игнор
    - rel начинается с "игнор/"
    """
    if rel_dir_posix == "":
        return False

    for ign in IGNORE_DIRS:
        ign_norm = normalize_rel_posix(ign)
        if not ign_norm:
            continue
        if rel_dir_posix == ign_norm:
            return True
        if rel_dir_posix.startswith(ign_norm + "/"):
            return True
    return False


def is_ignored_file_rel(rel_file_posix: str, name: str) -> bool:
    """
    IGNORE_FILES поддерживает два формата:
    - "file.ext"   -> игнор по имени везде
    - "a/b/c.ext"  -> игнор по относительному пути от корня проекта
    """
    # базовые секреты: .env и любые .env.* кроме .env.example
    if name == ".env":
        return True
    if name.startswith(".env.") and name != ".env.example":
        return True

    for ign in IGNORE_FILES:
        ign_norm = normalize_rel_posix(ign)
        if not ign_norm:
            continue
        if "/" in ign_norm:
            if rel_file_posix == ign_norm:
                return True
        else:
            if name == ign_norm:
                return True

    return False


def is_allowed_file(path: Path) -> bool:
    name = path.name

    # базовые секреты: .env и любые .env.* кроме .env.example
    if name == ".env":
        return False
    if name.startswith(".env.") and name != ".env.example":
        return False

    if path.is_symlink():
        return False

    # разрешаем некоторые файлы без расширения / dotfiles
    if name in ALLOWED_NAMES:
        return True

    if not ALLOWED_EXTS:
        return True

    if name.lower() == "dockerfile":
        return True

    return path.suffix.lower() in ALLOWED_EXTS


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def resolve_case_insensitive(root: Path, rel: str) -> Optional[Path]:
    """Найти путь без учёта регистра (readme.md -> README.md)."""
    rel_path = Path(rel)
    cur = root
    for part in rel_path.parts:
        if not cur.is_dir():
            return None
        direct = cur / part
        if direct.exists():
            cur = direct
            continue

        part_low = part.lower()
        found = None
        try:
            for child in cur.iterdir():
                if child.name.lower() == part_low:
                    found = child
                    break
        except Exception:
            return None

        if found is None:
            return None
        cur = found
    return cur


def walk_dir_collect_files(base: Path, root: Path, out_path: Path) -> Iterable[Path]:
    if not base.exists():
        return []

    files: List[Path] = []

    base = base.resolve()
    root = root.resolve()
    out_path = out_path.resolve()

    for dirpath, dirnames, filenames in os.walk(base, topdown=True):
        cur_dir = Path(dirpath).resolve()

        try:
            rel_dir = cur_dir.relative_to(root).as_posix()
        except Exception:
            dirnames[:] = []
            continue

        if is_ignored_dir_rel(rel_dir):
            dirnames[:] = []
            continue

        pruned: List[str] = []
        for d in dirnames:
            child = (cur_dir / d).resolve()
            try:
                child_rel = child.relative_to(root).as_posix()
            except Exception:
                continue
            if is_ignored_dir_rel(child_rel):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fname in filenames:
            p = (cur_dir / fname).resolve()
            if not p.is_file():
                continue

            if p == out_path:
                continue

            try:
                rel_file = p.relative_to(root).as_posix()
            except Exception:
                continue

            if is_ignored_file_rel(rel_file, p.name):
                continue

            if not is_allowed_file(p):
                continue

            if MAX_FILE_SIZE_BYTES and p.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue

            files.append(p)

    return files


def unique_paths(paths: Iterable[Path]) -> List[Path]:
    seen: Set[str] = set()
    result: List[Path] = []
    for p in paths:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


def collect_files(project_root: Path, out_path: Path) -> List[Path]:
    missing: List[str] = []
    to_collect: List[Path] = []

    root = project_root.resolve()
    out_path = out_path.resolve()

    # 1) INCLUDE_DIRS -> рекурсивно
    if ALL_FILES:
        for d in INCLUDE_DIRS:
            d_norm = normalize_rel_posix(d)
            if d_norm in ("", "."):
                base = root
            else:
                resolved = resolve_case_insensitive(root, d_norm)
                base = (resolved if resolved is not None else (root / d_norm))
            base = base.resolve()

            try:
                base_rel = base.relative_to(root).as_posix()
            except Exception:
                continue
            if is_ignored_dir_rel(base_rel):
                continue

            to_collect.extend(walk_dir_collect_files(base, root, out_path))

    # 2) INCLUDE_FILES -> явно
    for f in INCLUDE_FILES:
        f_norm = normalize_rel_posix(f)
        if f_norm in ("", "."):
            continue

        p = (root / f_norm).resolve()
        if not p.exists():
            p_ci = resolve_case_insensitive(root, f_norm)
            if p_ci is None:
                missing.append(f)
                continue
            p = p_ci.resolve()

        if p == out_path:
            continue

        if p.is_file():
            rel_file = p.relative_to(root).as_posix()
            if is_ignored_file_rel(rel_file, p.name):
                continue
            if not is_allowed_file(p):
                continue
            parent_rel = p.parent.relative_to(root).as_posix()
            if is_ignored_dir_rel(parent_rel):
                continue
            if MAX_FILE_SIZE_BYTES and p.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            to_collect.append(p)

    to_collect = unique_paths(to_collect)
    to_collect.sort(key=lambda p: p.resolve().relative_to(root).as_posix())

    if missing:
        print("WARNING: не найдены (проверь регистр/путь):")
        for m in missing:
            print(f" - {m}")

    return to_collect


def main() -> None:
    parser = argparse.ArgumentParser(description="Сборка проекта в один файл")
    parser.add_argument("--root", default=None, help="Корень проекта (если не задан — ищем по pyproject.toml от расположения скрипта)")
    parser.add_argument(
        "--out",
        default=DEFAULT_OUTPUT,
        help=f"Имя выходного файла (создаётся рядом со скриптом, по умолчанию {DEFAULT_OUTPUT})"
    )
    args = parser.parse_args()

    project_root = detect_project_root(args.root)

    script_dir = Path(__file__).resolve().parent
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (script_dir / out_path).resolve()
    else:
        out_path = out_path.resolve()

    files = collect_files(project_root, out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        header = f"# Bundled from project root: {project_root.as_posix()}\n"
        out.write(header + "\n")
        for i, p in enumerate(files):
            rel = p.resolve().relative_to(project_root).as_posix()
            out.write(f"# {rel}\n")
            try:
                content = read_text(p)
            except Exception as e:
                content = f"<<ERROR READING FILE: {e}>>"
            out.write(content.rstrip() + "\n")
            if i != len(files) - 1:
                out.write("\n")

    print(f"OK: собрано файлов: {len(files)} → {out_path}")
    print(f"ROOT = {project_root.as_posix()}")
    print(f"SCRIPT_DIR = {script_dir.as_posix()}")


if __name__ == "__main__":
    main()