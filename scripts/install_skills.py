#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Install, uninstall, or inspect research-papers skills/plugins for Codex, Claude, and Gemini.

Usage:
  uv run scripts/install_skills.py install
  uv run scripts/install_skills.py uninstall
  uv run scripts/install_skills.py doctor

By default, install/uninstall targets Codex, Claude, and Gemini user skill dirs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MARKER_FILENAME = ".research-papers-plugin-install.json"
DEFAULT_PLATFORMS = ("codex", "claude", "gemini")
TOOLING_REQUIREMENTS = {
    "uv": {
        "required": True,
        "reason": "installer/runtime entrypoint",
        "skills": ["all"],
    },
    "python": {
        "required": True,
        "reason": "bundled helper scripts",
        "skills": ["all"],
    },
    "curl": {
        "required": False,
        "reason": "paper download fallback",
        "skills": ["paper-retriever", "paper-process"],
    },
    "magick": {
        "required": False,
        "reason": "PDF to page-image conversion",
        "skills": ["paper-reader", "paper-process", "process-new-papers", "process-leads"],
    },
    "pdfinfo": {
        "required": False,
        "reason": "paper page-count inspection",
        "skills": ["paper-reader", "paper-process", "process-new-papers", "process-leads"],
    },
}


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path


@dataclass(frozen=True)
class ClaudePlugin:
    name: str


@dataclass(frozen=True)
class ClaudeMarketplace:
    name: str
    path: Path
    plugins: tuple[ClaudePlugin, ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def discover_skills(root: Path) -> list[Skill]:
    plugins_root = root / "plugins"
    skills: list[Skill] = []
    seen: dict[str, Path] = {}

    for skill_md in sorted(plugins_root.glob("*/skills/*/SKILL.md")):
        skill_dir = skill_md.parent
        name = skill_dir.name
        if name in seen and seen[name] != skill_dir:
            raise RuntimeError(
                f"Duplicate skill name '{name}' at {skill_dir} and {seen[name]}"
            )
        seen[name] = skill_dir
        skills.append(Skill(name=name, path=skill_dir))

    if not skills:
        raise RuntimeError(f"No skills discovered under {plugins_root}")

    return skills


def discover_claude_marketplace(root: Path) -> ClaudeMarketplace:
    manifest_path = root / ".claude-plugin" / "marketplace.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing Claude marketplace manifest: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = data.get("name")
    plugins = data.get("plugins")
    if not isinstance(name, str) or not name:
        raise RuntimeError(f"Invalid marketplace name in {manifest_path}")
    if not isinstance(plugins, list) or not plugins:
        raise RuntimeError(f"No plugins listed in {manifest_path}")

    discovered: list[ClaudePlugin] = []
    seen: set[str] = set()
    for plugin in plugins:
        plugin_name = plugin.get("name") if isinstance(plugin, dict) else None
        if not isinstance(plugin_name, str) or not plugin_name:
            raise RuntimeError(f"Invalid plugin entry in {manifest_path}: {plugin!r}")
        if plugin_name in seen:
            raise RuntimeError(f"Duplicate Claude plugin name '{plugin_name}' in {manifest_path}")
        seen.add(plugin_name)
        discovered.append(ClaudePlugin(name=plugin_name))

    return ClaudeMarketplace(name=name, path=manifest_path, plugins=tuple(discovered))


def target_root(platform_name: str) -> Path:
    home = Path.home()
    if platform_name == "codex":
        return home / ".agents" / "skills"
    if platform_name == "claude":
        return home / ".claude" / "skills"
    if platform_name == "gemini":
        return home / ".gemini" / "skills"
    raise ValueError(f"Unknown platform: {platform_name}")


def run_cli(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )


def claude_cli_cmd(*args: str) -> list[str]:
    for candidate in ("claude", "claude.cmd", "claude.exe"):
        path = shutil.which(candidate)
        if path:
            return [path, *args]

    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if pwsh is None:
        raise RuntimeError("Claude CLI not found on PATH")

    probe = run_cli([pwsh, "-NoProfile", "-Command", "(Get-Command claude).Source"])
    ensure_success(probe, "resolve claude executable")
    source = probe.stdout.strip()
    if not source:
        raise RuntimeError("Claude CLI not found on PATH")

    if source.lower().endswith(".ps1"):
        return [pwsh, "-NoProfile", "-File", source, *args]

    return [source, *args]


def format_cli_output(result: subprocess.CompletedProcess[str]) -> str:
    parts = [result.stdout.strip(), result.stderr.strip()]
    return "\n".join(part for part in parts if part).strip()


def ensure_success(
    result: subprocess.CompletedProcess[str],
    context: str,
    *,
    accept_patterns: tuple[str, ...] = (),
) -> str:
    combined = format_cli_output(result)
    lowered = combined.lower()
    if result.returncode == 0:
        return combined
    if any(pattern in lowered for pattern in accept_patterns):
        return combined
    raise RuntimeError(f"{context} failed:\n{combined or f'exit code {result.returncode}'}")


def parse_claude_plugin_list(output: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^\s*>\s+(.+)$", line)
        if match:
            if current:
                entries.append(current)
            current = {"plugin": match.group(1).strip()}
            continue
        if current is None:
            continue
        field_match = re.match(r"^\s+([A-Za-z]+):\s+(.*)$", line)
        if field_match:
            current[field_match.group(1).lower()] = field_match.group(2).strip()

    if current:
        entries.append(current)

    return entries


def list_claude_plugins() -> list[dict[str, str]]:
    result = run_cli(claude_cli_cmd("plugin", "list"))
    ensure_success(result, "claude plugin list")
    return parse_claude_plugin_list(result.stdout)


def claude_plugin_installed(
    entries: list[dict[str, str]],
    plugin_name: str,
    marketplace_name: str,
    *,
    scope: str = "user",
) -> bool:
    plugin_id = f"{plugin_name}@{marketplace_name}"
    for entry in entries:
        if entry.get("plugin") != plugin_id:
            continue
        if entry.get("scope", "").lower() == scope:
            return True
    return False


def install_claude_plugins(
    root: Path,
    marketplace: ClaudeMarketplace,
    force: bool,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []

    add_result = run_cli(
        claude_cli_cmd(
            "plugin",
            "marketplace",
            "add",
            str(root),
            "--scope",
            "user",
        )
    )
    add_output = ensure_success(
        add_result,
        "claude plugin marketplace add",
        accept_patterns=("already exists", "already added", "already configured"),
    )
    add_status = "added" if add_result.returncode == 0 else "unchanged"
    if add_output:
        add_status = f"{add_status} ({add_output.splitlines()[0]})"
    results.append((f"marketplace:{marketplace.name}", add_status))

    installed = list_claude_plugins()
    for plugin in marketplace.plugins:
        plugin_id = f"{plugin.name}@{marketplace.name}"
        if claude_plugin_installed(installed, plugin.name, marketplace.name) and not force:
            results.append((plugin.name, "unchanged"))
            continue

        if force and claude_plugin_installed(installed, plugin.name, marketplace.name):
            remove_result = run_cli(
                claude_cli_cmd("plugin", "uninstall", plugin_id, "--scope", "user")
            )
            ensure_success(
                remove_result,
                f"claude plugin uninstall {plugin_id}",
                accept_patterns=("not installed", "not found"),
            )

        install_result = run_cli(
            claude_cli_cmd("plugin", "install", plugin_id, "--scope", "user")
        )
        install_output = ensure_success(
            install_result,
            f"claude plugin install {plugin_id}",
            accept_patterns=("already installed",),
        )
        status = "installed" if install_result.returncode == 0 else "unchanged"
        if install_output:
            status = f"{status} ({install_output.splitlines()[0]})"
        results.append((plugin.name, status))

    return results


def uninstall_claude_plugins(
    marketplace: ClaudeMarketplace,
    force: bool,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    installed = list_claude_plugins()

    for plugin in marketplace.plugins:
        plugin_id = f"{plugin.name}@{marketplace.name}"
        if not claude_plugin_installed(installed, plugin.name, marketplace.name):
            results.append((plugin.name, "missing"))
            continue

        remove_result = run_cli(
            claude_cli_cmd("plugin", "uninstall", plugin_id, "--scope", "user")
        )
        remove_output = ensure_success(
            remove_result,
            f"claude plugin uninstall {plugin_id}",
            accept_patterns=("not installed", "not found"),
        )
        status = "removed" if remove_result.returncode == 0 else "missing"
        if remove_output:
            status = f"{status} ({remove_output.splitlines()[0]})"
        results.append((plugin.name, status))

    marketplace_remove = run_cli(
        claude_cli_cmd("plugin", "marketplace", "remove", marketplace.name)
    )
    remove_output = format_cli_output(marketplace_remove)
    if marketplace_remove.returncode == 0:
        status = "removed"
    else:
        lowered = remove_output.lower()
        if any(token in lowered for token in ("not found", "does not exist", "unknown marketplace")):
            status = "missing"
        elif force:
            status = f"skipped ({remove_output.splitlines()[0]})" if remove_output else "skipped"
        else:
            raise RuntimeError(
                "claude plugin marketplace remove failed:\n"
                + (remove_output or f"exit code {marketplace_remove.returncode}")
            )
    results.append((f"marketplace:{marketplace.name}", status))
    return results


def managed_marker(dest: Path) -> Path:
    return dest / MARKER_FILENAME


def marker_payload(source: Path, platform_name: str) -> dict[str, str]:
    return {
        "installed_from": str(source.resolve()),
        "platform": platform_name,
        "installer": str(Path(__file__).resolve()),
    }


def load_marker(dest: Path) -> dict[str, str] | None:
    marker = managed_marker(dest)
    if not marker.is_file():
        return None
    try:
        return json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        return None


def remove_existing(dest: Path) -> None:
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)


def is_managed_copy(dest: Path, source: Path) -> bool:
    payload = load_marker(dest)
    return payload is not None and payload.get("installed_from") == str(source.resolve())


def is_matching_symlink(dest: Path, source: Path) -> bool:
    if not dest.is_symlink():
        return False
    try:
        return dest.resolve() == source.resolve()
    except OSError:
        return False


def install_skill(skill: Skill, dest_root: Path, platform_name: str, force: bool) -> str:
    dest_root.mkdir(parents=True, exist_ok=True)
    dest = dest_root / skill.name

    if dest.exists() or dest.is_symlink():
        if is_matching_symlink(dest, skill.path) or is_managed_copy(dest, skill.path):
            return "unchanged"
        if not force:
            raise RuntimeError(
                f"Destination exists and is not managed by this installer: {dest}"
            )
        remove_existing(dest)

    try:
        os.symlink(str(skill.path), str(dest), target_is_directory=True)
        return "linked"
    except OSError:
        shutil.copytree(skill.path, dest, symlinks=False)
        managed_marker(dest).write_text(
            json.dumps(marker_payload(skill.path, platform_name), indent=2) + "\n",
            encoding="utf-8",
        )
        return "copied"


def uninstall_skill(skill: Skill, dest_root: Path, force: bool) -> str:
    dest = dest_root / skill.name
    if not dest.exists() and not dest.is_symlink():
        return "missing"

    if is_matching_symlink(dest, skill.path) or is_managed_copy(dest, skill.path):
        remove_existing(dest)
        return "removed"

    if force:
        remove_existing(dest)
        return "removed-force"

    return "skipped"


def run_doctor(skills: list[Skill]) -> int:
    root = repo_root()
    marketplace = discover_claude_marketplace(root)
    print("Skill discovery:")
    for skill in skills:
        print(f"  - {skill.name}: {skill.path}")

    print("\nClaude marketplace:")
    print(f"  - {marketplace.name}: {marketplace.path}")
    for plugin in marketplace.plugins:
        print(f"      plugin: {plugin.name}")

    print("\nTooling:")
    failures = 0
    for tool, meta in TOOLING_REQUIREMENTS.items():
        if tool == "python":
            found = sys.executable
        else:
            found = shutil.which(tool)
        status = "OK" if found else ("MISSING" if meta["required"] else "WARN")
        skills_text = ", ".join(meta["skills"])
        print(
            f"  - {tool}: {status}"
            f" | {meta['reason']}"
            f" | affects: {skills_text}"
        )
        if found:
            print(f"      {found}")
        elif meta["required"]:
            failures += 1

    claude_path = shutil.which("claude")
    status = "OK" if claude_path else "WARN"
    print("  - claude: " + status + " | native marketplace install path | affects: claude")
    if claude_path:
        print(f"      {claude_path}")

    print("\nTarget roots:")
    for platform_name in DEFAULT_PLATFORMS:
        if platform_name == "claude":
            print("  - claude: native plugin install via `claude plugin marketplace add/install`")
        else:
            print(f"  - {platform_name}: {target_root(platform_name)}")

    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("install", "uninstall", "doctor"),
        help="Action to run",
    )
    parser.add_argument(
        "--platform",
        dest="platforms",
        choices=DEFAULT_PLATFORMS,
        action="append",
        help="Limit to one or more platforms (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing conflicting installs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    skills = discover_skills(root)
    marketplace = discover_claude_marketplace(root)
    platforms = tuple(args.platforms or DEFAULT_PLATFORMS)

    if args.command == "doctor":
        return run_doctor(skills)

    for platform_name in platforms:
        if platform_name == "claude":
            print(f"{args.command.title()} claude plugins via native Claude CLI")
            claude_cli_cmd("plugin", "list")
            if args.command == "install":
                claude_results = install_claude_plugins(root, marketplace, args.force)
            else:
                claude_results = uninstall_claude_plugins(marketplace, args.force)
            for name, result in claude_results:
                print(f"  - {name}: {result}")
            continue

        dest_root = target_root(platform_name)
        print(f"{args.command.title()} {platform_name} skills -> {dest_root}")
        for skill in skills:
            if args.command == "install":
                result = install_skill(skill, dest_root, platform_name, args.force)
            else:
                result = uninstall_skill(skill, dest_root, args.force)
            print(f"  - {skill.name}: {result}")

    if args.command == "install":
        print("\nRestart Codex/Claude/Gemini if they are already running.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
