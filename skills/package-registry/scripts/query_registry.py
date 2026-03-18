#!/usr/bin/env python3
"""Query package registries (PyPI, npm) for version and release date."""
import argparse
import json
import urllib.request
import urllib.error


def query_pypi(package: str) -> dict:
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    info = data.get("info", {})
    version = info.get("version", "unknown")
    # PyPI doesn't have release date in info; check releases
    releases = data.get("releases", {})
    release_dates = []
    for ver, files in releases.items():
        for f in files:
            if f.get("upload_time"):
                release_dates.append(f["upload_time"])
                break
    release_date = max(release_dates) if release_dates else "unknown"
    return {"version": version, "release_date": release_date}


def query_npm(package: str) -> dict:
    url = f"https://registry.npmjs.org/{package}/latest"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    version = data.get("version", "unknown")
    release_date = data.get("time", {}).get(version, "unknown")
    return {"version": version, "release_date": release_date}


def main():
    parser = argparse.ArgumentParser(description="Query package registries")
    parser.add_argument("--registry", choices=["pypi", "npm"], required=True)
    parser.add_argument("--package", required=True, help="Package name")
    args = parser.parse_args()

    try:
        if args.registry == "pypi":
            result = query_pypi(args.package)
        else:
            result = query_npm(args.package)
        print(f"Version: {result['version']}")
        print(f"Release date: {result['release_date']}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Package '{args.package}' not found in {args.registry}")
        else:
            print(f"Error: HTTP {e.code} - {e.reason}")
        raise SystemExit(1)
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
