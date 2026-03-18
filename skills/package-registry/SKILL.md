---
name: package-registry
description: Query package registries (PyPI, npm) for package information including latest versions, release dates, and metadata. Use when the user asks about package versions or release info.
---

# Package Registry

Query package registries for package information including latest versions, release dates, and metadata.

## API Endpoints

### PyPI JSON API

```bash
curl -s "https://pypi.org/pypi/{package}/json"
```

Returns JSON with `info.version`, `releases`, and `urls` for the package.

### npm Registry

```bash
curl -s "https://registry.npmjs.org/{package}/latest"
```

Returns JSON with `version`, `dist.tarball`, and other metadata for the latest release.

## Script

For convenience, use the script:

```bash
python scripts/query_registry.py --registry pypi --package requests
python scripts/query_registry.py --registry npm --package lodash
```

The script prints version and release date from the API response.
