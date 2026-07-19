"""Fetch and parse the packwiz modpack from GitHub, plus Modrinth enrichment.

Shared by the dashboard Packwiz tab (read-only overview) and the
``sync_from_packwiz`` management command.
"""

import io
import re
import tarfile
import time
import tomllib
from dataclasses import asdict, dataclass, field
from typing import Optional

import requests
from django.conf import settings

from features.mods.models import Mod, PackwizSnapshot

_ARCHIVE_URL = "https://github.com/{repo}/archive/refs/heads/{branch}.tar.gz"
_MODS_PREFIX = "/mods/"
_REQUEST_TIMEOUT = 30


@dataclass
class PackwizEntry:
    """A single entry in the packwiz ``mods/`` folder."""

    filename: str
    name: str
    source: str  # "modrinth" | "curseforge" | "jar"
    modrinth_id: str = ""
    version_id: str = ""
    side: str = ""


def _archive_url() -> str:
    return _ARCHIVE_URL.format(
        repo=settings.PACKWIZ_REPO, branch=settings.PACKWIZ_BRANCH
    )


def _modrinth_headers() -> dict:
    return {"User-Agent": settings.MODRINTH_USER_AGENT}


def fetch_pack_entries() -> list[PackwizEntry]:
    """Download the pack archive once and parse every ``mods/`` entry.

    Uses the GitHub tarball (a single request) instead of fetching ~195
    individual files.
    """
    resp = requests.get(_archive_url(), timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()

    entries: list[PackwizEntry] = []
    with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            idx = member.name.find(_MODS_PREFIX)
            if idx == -1:
                continue
            rel = member.name[idx + len(_MODS_PREFIX) :]
            if "/" in rel:  # nested, not a direct mod entry
                continue

            if rel.endswith(".pw.toml"):
                fileobj = tar.extractfile(member)
                if fileobj is None:
                    continue
                entries.append(_parse_pw_toml(rel, fileobj.read()))
            elif rel.endswith(".jar"):
                entries.append(PackwizEntry(filename=rel, name=rel, source="jar"))

    entries.sort(key=lambda e: e.name.lower())
    return entries


def _parse_pw_toml(filename: str, raw: bytes) -> PackwizEntry:
    data = tomllib.loads(raw.decode("utf-8"))
    update = data.get("update", {})
    name = data.get("name", filename)
    side = data.get("side", "")

    if "modrinth" in update:
        m = update["modrinth"]
        return PackwizEntry(
            filename=filename,
            name=name,
            source="modrinth",
            modrinth_id=str(m.get("mod-id", "")),
            version_id=str(m.get("version", "")),
            side=side,
        )
    if "curseforge" in update:
        return PackwizEntry(
            filename=filename, name=name, source="curseforge", side=side
        )
    # A .pw.toml without a known update provider (rare) — treat as manual.
    return PackwizEntry(filename=filename, name=name, source="jar", side=side)


def refresh_snapshot() -> PackwizSnapshot:
    """Fetch the current pack state and persist it to the singleton snapshot."""
    entries = fetch_pack_entries()
    snapshot = PackwizSnapshot.load()
    snapshot.data = {"entries": [asdict(e) for e in entries]}
    snapshot.save()
    return snapshot


def snapshot_entries(snapshot: PackwizSnapshot) -> list[PackwizEntry]:
    """Deserialize stored snapshot data back into PackwizEntry objects."""
    return [PackwizEntry(**e) for e in snapshot.data.get("entries", [])]


# --- Dashboard classification ------------------------------------------------


@dataclass
class OverviewItem:
    name: str
    thumbnail_url: str = ""
    version: str = ""
    source: str = ""
    slug: str = ""


@dataclass
class PackOverview:
    synced: list[OverviewItem] = field(default_factory=list)
    jar: list[OverviewItem] = field(default_factory=list)
    removed: list[OverviewItem] = field(default_factory=list)
    pack_only: list[OverviewItem] = field(default_factory=list)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _thumb_url(mod: Optional[Mod]) -> str:
    if mod is not None and mod.thumbnail:
        return mod.thumbnail.url
    return ""


def classify_pack(entries: list[PackwizEntry], mods: list[Mod]) -> PackOverview:
    """Cross-reference pack entries against site mods into status buckets.

    Match key is the Modrinth id; falls back to a normalized name for mods that
    do not have an id yet (pre-sync bootstrap).
    """
    by_id = {m.modrinth_id: m for m in mods if m.modrinth_id}
    by_name = {_normalize(m.name): m for m in mods}
    matched: set[int] = set()
    overview = PackOverview()

    def _match(entry: PackwizEntry) -> Optional[Mod]:
        mod = by_id.get(entry.modrinth_id) if entry.modrinth_id else None
        if mod is None:
            mod = by_name.get(_normalize(entry.name))
        if mod is not None:
            matched.add(mod.pk)
        return mod

    for entry in entries:
        if entry.source in ("jar", "curseforge"):
            mod = _match(entry)
            overview.jar.append(
                OverviewItem(
                    name=entry.name,
                    thumbnail_url=_thumb_url(mod),
                    source=entry.source,
                    slug=mod.slug if mod else "",
                )
            )
            continue

        mod = _match(entry)
        if mod is not None:
            overview.synced.append(
                OverviewItem(
                    name=mod.name,
                    thumbnail_url=_thumb_url(mod),
                    version=mod.version,
                    source="modrinth",
                    slug=mod.slug,
                )
            )
        else:
            overview.pack_only.append(OverviewItem(name=entry.name, source="modrinth"))

    for mod in mods:
        if mod.pk not in matched:
            overview.removed.append(
                OverviewItem(
                    name=mod.name,
                    thumbnail_url=_thumb_url(mod),
                    version=mod.version,
                    slug=mod.slug,
                )
            )

    return overview


# --- Modrinth enrichment (used by the sync command, not the dashboard) -------


@dataclass
class ModrinthData:
    modrinth_id: str
    name: str
    version: str
    description: str
    body: str
    icon_url: str
    mod_url: str
    mod_wiki: str
    dependencies: list[str]


def enrich_from_modrinth(
    entries: list[PackwizEntry], backoff: float = 0.1
) -> dict[str, ModrinthData]:
    """Fetch Modrinth metadata for the given modrinth-sourced entries.

    Returns a mapping ``modrinth_id -> ModrinthData``. Skips entries whose
    project or version fetch fails.
    """
    mod_ids = [
        e.modrinth_id for e in entries if e.source == "modrinth" and e.modrinth_id
    ]
    if not mod_ids:
        return {}

    projects = _fetch_projects(mod_ids)

    result: dict[str, ModrinthData] = {}
    for entry in entries:
        if entry.source != "modrinth" or not entry.modrinth_id:
            continue
        project = projects.get(entry.modrinth_id)
        if project is None:
            continue

        version_number, dep_ids = _fetch_version(entry.version_id)
        time.sleep(backoff)

        result[entry.modrinth_id] = ModrinthData(
            modrinth_id=entry.modrinth_id,
            name=project.get("title", entry.name),
            version=version_number,
            description=project.get("description", ""),
            body=project.get("body", ""),
            icon_url=project.get("icon_url") or "",
            mod_url=_project_url(project) or (project.get("source_url") or ""),
            mod_wiki=project.get("wiki_url") or "",
            dependencies=_resolve_dependency_names(dep_ids),
        )
    return result


def _fetch_projects(mod_ids: list[str]) -> dict[str, dict]:
    """Batch-fetch project metadata, chunked to keep URLs short."""
    projects: dict[str, dict] = {}
    for chunk in _chunks(sorted(set(mod_ids)), 50):
        ids_param = "[" + ",".join(f'"{i}"' for i in chunk) + "]"
        resp = requests.get(
            f"{settings.MODRINTH_API}/projects",
            params={"ids": ids_param},
            headers=_modrinth_headers(),
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        for project in resp.json():
            projects[project["id"]] = project
    return projects


def _fetch_version(version_id: str) -> tuple[str, list[str]]:
    if not version_id:
        return "", []
    resp = requests.get(
        f"{settings.MODRINTH_API}/version/{version_id}",
        headers=_modrinth_headers(),
        timeout=_REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        return "", []
    data = resp.json()
    version_number = data.get("version_number", "")
    dep_ids = [
        d["project_id"]
        for d in data.get("dependencies", [])
        if d.get("project_id") and d.get("dependency_type") == "required"
    ]
    return version_number, dep_ids


def _resolve_dependency_names(project_ids: list[str]) -> list[str]:
    if not project_ids:
        return []
    projects = _fetch_projects(project_ids)
    return sorted(projects[pid]["title"] for pid in project_ids if pid in projects)


def _project_url(project: dict) -> Optional[str]:
    slug = project.get("slug")
    return f"https://modrinth.com/mod/{slug}" if slug else None


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]
