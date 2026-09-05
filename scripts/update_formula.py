#!/usr/bin/env python3
"""
Regenerate Formula/net-benchmark.rb against the current PyPI release.

Run manually:  python3 scripts/update_formula.py
Run in CI:      same, then the workflow diffs the file and opens a PR
                only if something actually changed.

Exits 0 with no file changes if the formula is already current — this is
what makes the scheduled workflow safe to run daily without spamming PRs.
"""
import json
import re
import sys
import tempfile
import urllib.request
import subprocess
import venv
from pathlib import Path

PACKAGE = "net-benchmark"
FORMULA_PATH = Path(__file__).parent.parent / "Formula" / "net-benchmark.rb"


def pypi_json(name, version=None):
    url = f"https://pypi.org/pypi/{name}/{version}/json" if version else f"https://pypi.org/pypi/{name}/json"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def sdist_info(name, version):
    d = pypi_json(name, version)
    for f in d["urls"]:
        if f["packagetype"] == "sdist":
            return f["url"], f["digests"]["sha256"]
    return None, None


def current_formula_version():
    if not FORMULA_PATH.exists():
        return None
    text = FORMULA_PATH.read_text()
    m = re.search(r"net_benchmark-([0-9.]+)\.tar\.gz", text)
    return m.group(1) if m else None


def resolve_dependencies(version):
    """Install the target version into a throwaway venv and read back the
    exact resolved dependency set — the same real-install technique used
    when this formula was first built, not a guess from requires_dist."""
    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.create(venv_dir, with_pip=True)
        pip = venv_dir / "bin" / "pip"
        subprocess.run(
            [str(pip), "install", "--quiet", f"{PACKAGE}=={version}"],
            check=True,
        )
        out = subprocess.run(
            [str(pip), "list", "--format=freeze"],
            check=True, capture_output=True, text=True,
        ).stdout
    deps = {}
    for line in out.splitlines():
        if "==" not in line:
            continue
        name, ver = line.strip().split("==")
        if name.lower() in (PACKAGE.lower(), "pip", "setuptools"):
            continue
        deps[name] = ver
    return deps


def build_resource_block(name, version):
    url, sha = sdist_info(name, version)
    if not url:
        print(f"::warning::no sdist for {name}=={version}, skipping — "
              f"formula will need this resource added by hand", file=sys.stderr)
        return None
    return f'  resource "{normalize(name)}" do\n    url "{url}"\n    sha256 "{sha}"\n  end\n'


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def main():
    latest = pypi_json(PACKAGE)["info"]["version"]
    current = current_formula_version()

    if current == latest:
        print(f"Formula already current at {latest}, nothing to do.")
        return

    print(f"Formula is at {current or 'unknown'}, PyPI has {latest} — regenerating.")

    main_url, main_sha = sdist_info(PACKAGE, latest)
    if not main_url:
        print(f"::error::no sdist found for {PACKAGE}=={latest}", file=sys.stderr)
        sys.exit(1)

    deps = resolve_dependencies(latest)
    resources = []
    for name in sorted(deps, key=str.lower):
        block = build_resource_block(name, deps[name])
        if block:
            resources.append(block)

    if not FORMULA_PATH.exists():
        print(f"::error::{FORMULA_PATH} does not exist — cannot regenerate a formula that was never created. Run this only after the formula exists.", file=sys.stderr)
        sys.exit(1)

    text = FORMULA_PATH.read_text()

    # Swap the main package's url/sha256 (the two lines right after `class`,
    # before the first `depends_on`).
    text = re.sub(
        r'url "https://files\.pythonhosted\.org/packages/[^"]+"\n  sha256 "[a-f0-9]+"',
        f'url "{main_url}"\n  sha256 "{main_sha}"',
        text,
        count=1,
    )

    # Replace the entire resource block region (everything from the first
    # `resource "..." do` to the line before `def install`).
    new_resources = "\n" + "\n".join(resources) + "\n"
    text = re.sub(
        r'\n(  resource "[^"]+" do\n.*?\n  end\n\s*)+\n(?=  def install)',
        new_resources + "\n",
        text,
        flags=re.DOTALL,
    )

    FORMULA_PATH.write_text(text)
    print(f"Formula regenerated for {latest}: {len(resources)} resources.")


if __name__ == "__main__":
    main()
