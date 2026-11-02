from pathlib import Path
import json
import sys
import urllib.error
import urllib.request
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def check_requirements(file_path="requirements.txt"):
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()

    total_checked = 0
    not_found = 0
    incompatible_311 = 0

    highest_pkg = None
    highest_min_ver = None
    highest_min_str = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        total_checked += 1
        name, version = line.split("==", 1)
        url = f"https://pypi.org/pypi/{name}/{version}/json"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                not_found += 1
                continue
            raise

        requires_python = data.get("info", {}).get("requires_python")

        if requires_python:
            spec_set = SpecifierSet(requires_python)

            if not spec_set.contains("3.11"):
                incompatible_311 += 1

            for spec in spec_set:
                if spec.operator in (">=", ">", "==", "~="):
                    ver = Version(spec.version)
                    if highest_min_ver is None or ver > highest_min_ver:
                        highest_min_ver = ver
                        highest_pkg = f"{name}=={version}"
                        highest_min_str = f"{spec.operator}{spec.version}"

    print(f"Dependencies checked: {total_checked}")
    print(f"Not found on PyPI: {not_found}")
    print(f"Incompatible with Python 3.11: {incompatible_311}")
    if highest_pkg:
        print(f"Highest requirement: {highest_pkg} ({highest_min_str})")


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"
    check_requirements(target_file)