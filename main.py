
import json
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote

from packaging.specifiers import SpecifierSet
from packaging.version import Version


PYTHON_VERSION = Version("3.11")


def get_pypi_data(url):
    try:
        with urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def minimum_python_version(specifiers):
    versions = []

    for spec in specifiers:
        if spec.operator in (">=", ">", "~=", "=="):
            try:
                versions.append(Version(spec.version))
            except Exception:
                pass

    return max(versions) if versions else Version("0")


def check_dependencies(filename="requirements.txt"):
    checked = 0
    not_found = 0
    incompatible = 0
    highest = None

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "==" not in line:
                continue

            name, version = line.split("==", 1)
            name = name.strip()
            version = version.strip()

            checked += 1

            package_url = (
                f"https://pypi.org/pypi/{quote(name, safe='')}/json"
            )

            package_data = get_pypi_data(package_url)

            if package_data is None:
                not_found += 1
                continue

            release_url = (
                f"https://pypi.org/pypi/"
                f"{quote(name, safe='')}/"
                f"{quote(version, safe='')}/json"
            )

            release_data = get_pypi_data(release_url)

            if release_data is None:
                not_found += 1
                continue

            requires_python = (
                release_data["info"].get("requires_python") or ""
            )

            if not requires_python:
                continue

            specifiers = SpecifierSet(requires_python)

            if not specifiers.contains(PYTHON_VERSION):
                incompatible += 1

            minimum = minimum_python_version(specifiers)

            if highest is None or minimum > highest[0]:
                highest = (minimum, name, version, requires_python)

    print("Dependencies checked:", checked)
    print("Not found on PyPI:", not_found)
    print("Incompatible with Python 3.11:", incompatible)

    if highest:
        _, name, version, requirement = highest
        print(
            f"Highest requirement: "
            f"{name}=={version} ({requirement})"
        )


if __name__ == "__main__":
    check_dependencies()
