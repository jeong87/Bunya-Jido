from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore

IGNORE_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".venv", "venv", "env", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", "node_modules", "dist", "build",
    "site", ".next", ".turbo", ".parcel-cache", "coverage", ".coverage", "htmlcov", ".eggs",
}

CONFIG_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt",
    "Pipfile", "poetry.lock", "uv.lock", "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Makefile", "tox.ini", "noxfile.py",
    ".pre-commit-config.yaml", "mkdocs.yml", "mkdocs.yaml",
}

RUNTIME_DIR_HINTS = {"logs", "log", "state", "runs", "run", "artifacts", "outputs", "output", "experiments", "results", "checkpoints"}
DATA_DIR_HINTS = {"data", "datasets", "dataset", "notebooks", "notebook", "assets", "static"}
HEAVY_DATA_DIR_HINTS = {"data", "datasets", "dataset", "notebooks", "notebook"}
DOC_DIR_HINTS = {"docs", "doc", "wiki", "notes", "notebooks"}
TEST_DIR_HINTS = {"tests", "test", "spec", "specs"}
SRC_DIR_HINTS = {"src", "lib", "app", "apps", "services", "server", "client", "backend", "frontend"}

STDLIB_MODULES = set(getattr(sys, "stdlib_module_names", set()))

API_HINTS = {
    "openai": ("External OpenAI API", "OPENAI"),
    "anthropic": ("External Anthropic API", "ANTHROPIC"),
    "google.generativeai": ("External Gemini API", "GEMINI"),
    "google.genai": ("External Gemini API", "GEMINI"),
    "gemini": ("External Gemini API", "GEMINI"),
    "groq": ("External Groq API", "GROQ"),
    "cohere": ("External Cohere API", "COHERE"),
    "mistral": ("External Mistral API", "MISTRAL"),
    "ollama": ("Local Ollama / Model Server", "OLLAMA"),
    "qwen": ("Local Qwen / Model Server", "QWEN"),
    "llama": ("Local Llama / Model Server", "LLAMA"),
    "vllm": ("Local vLLM Server", "VLLM"),
    "transformers": ("Hugging Face / Transformers", "HF"),
    "huggingface": ("Hugging Face Hub", "HF"),
    "boto3": ("AWS / Bedrock API", "AWS"),
    "azure": ("Azure API", "AZURE"),
}

PLANE_BY_KIND = {
    "root": "repo",
    "repo": "repo",
    "directory": "repo",
    "package": "repo",
    "entrypoint": "code",
    "module": "code",
    "class": "code",
    "function": "code",
    "document": "docs",
    "config": "config",
    "test": "tests",
    "runtime": "runtime",
    "artifact": "runtime",
    "data": "data",
    "external": "external",
    "api_provider": "external",
    "meta": "meta",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(text: str, max_len: int = 96) -> str:
    text = str(text).replace(os.sep, "/")
    text = re.sub(r"[^A-Za-z0-9_.:/@+-]+", "-", text).strip("-")
    if not text:
        text = "node"
    if len(text) > max_len:
        h = hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()[:8]
        text = text[: max_len - 9].rstrip("-") + "-" + h
    return text


def read_text(path: Path, limit: int = 450_000) -> str:
    try:
        raw = path.read_bytes()
    except Exception:
        return ""
    if len(raw) > limit:
        raw = raw[:limit]
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc, errors="replace")
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


@dataclass
class Node:
    id: str
    label: str
    type: str
    plane: str
    description: str = ""
    source_path: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = ""
    major: bool = False
    degree: int = 0
    size: float = 7.0

    def to_json(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["tags"] = sorted(set(self.tags))
        return d


@dataclass
class Edge:
    id: str
    source: str
    target: str
    relation: str
    lens: str
    note: str = ""
    confidence: str = "deterministic"
    directed: bool = True
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self, labels: dict[str, str]) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "source_label": labels.get(self.source, self.source),
            "target_label": labels.get(self.target, self.target),
            "relation": self.relation,
            "lens": self.lens,
            "note": self.note,
            "confidence": self.confidence,
            "directed": self.directed,
            "evidence": self.evidence,
        }


class GraphBuilder:
    def __init__(self, root: Path, project_name: str | None = None) -> None:
        self.root = root.resolve()
        self.project_name = project_name or self.root.name
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.edge_seen: set[tuple[str, str, str, str]] = set()
        self.path_to_node: dict[str, str] = {}
        self.module_to_node: dict[str, str] = {}
        self.defined_symbols: dict[str, list[str]] = defaultdict(list)
        self.root_id = self.add_node(
            f"repo:{self.project_name}", self.project_name, "repo", "repo",
            description="Repository root scanned by Bunya-Jido.",
            source_path=".", tags=["repo", "root"], major=True, size=18,
        )

    def relpath(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except Exception:
            return path.as_posix()

    def add_node(self, node_id: str, label: str, type_: str, plane: str | None = None, **kwargs: Any) -> str:
        node_id = slug(node_id, 120)
        plane = plane or PLANE_BY_KIND.get(type_, "unknown")
        tags = list(kwargs.pop("tags", []))
        tags.extend([f"type/{type_}", f"plane/{plane}"])
        if node_id in self.nodes:
            n = self.nodes[node_id]
            n.tags = sorted(set(n.tags + tags))
            for k, v in kwargs.items():
                if hasattr(n, k) and v and not getattr(n, k):
                    setattr(n, k, v)
            if kwargs.get("major"):
                n.major = True
            if kwargs.get("size") and kwargs["size"] > n.size:
                n.size = kwargs["size"]
            return node_id
        self.nodes[node_id] = Node(node_id, label, type_, plane, tags=tags, **kwargs)
        return node_id

    def add_edge(self, source: str, target: str, relation: str, lens: str, note: str = "", evidence: dict[str, Any] | None = None, confidence: str = "deterministic") -> None:
        if not source or not target or source == target:
            return
        key = (source, target, relation, lens)
        if key in self.edge_seen:
            return
        self.edge_seen.add(key)
        self.edges.append(Edge(
            id=f"e{len(self.edges):05d}", source=source, target=target, relation=relation, lens=lens,
            note=note, confidence=confidence, evidence=[evidence] if evidence else []
        ))

    def add_file_node(self, path: Path, type_: str, plane: str | None = None, label: str | None = None, major: bool = False) -> str:
        rel = self.relpath(path)
        nid = self.add_node(f"{type_}:{rel}", label or path.name, type_, plane, source_path=rel, major=major)
        self.path_to_node[rel] = nid
        return nid

    def finish(self, max_nodes: int | None = None, max_edges: int | None = None, show_root: bool = False) -> dict[str, Any]:
        # Degree/size
        deg = Counter()
        for e in self.edges:
            if e.source in self.nodes and e.target in self.nodes:
                deg[e.source] += 1
                deg[e.target] += 1
        for node_id, n in self.nodes.items():
            n.degree = deg[node_id]
            if not n.major:
                n.size = max(n.size, min(17, 6 + (deg[node_id] ** 0.58)))
            else:
                n.size = max(n.size, min(26, 14 + (deg[node_id] ** 0.5)))

        nodes = list(self.nodes.values())
        if not show_root:
            nodes = [n for n in nodes if n.id != self.root_id]
            rootless_ids = {n.id for n in nodes}
            self.edges = [e for e in self.edges if e.source in rootless_ids and e.target in rootless_ids]
        if max_nodes and len(nodes) > max_nodes:
            # Keep root, major nodes, and high-degree nodes.
            keep = sorted(nodes, key=lambda n: (n.id == self.root_id, n.major, n.degree, n.size), reverse=True)[:max_nodes]
            keep_ids = {n.id for n in keep}
            nodes = keep
            edges = [e for e in self.edges if e.source in keep_ids and e.target in keep_ids]
        else:
            keep_ids = set(self.nodes)
            edges = list(self.edges)
        if max_edges and len(edges) > max_edges:
            # Prefer non-structure edges, then high-degree endpoints.
            priority = {"api_calls": 5, "calls": 4, "uses_module": 3, "tested_by": 3, "reads": 2, "writes": 2, "contains": 0, "defines": 1, "documents": 1}
            edges = sorted(edges, key=lambda e: (priority.get(e.relation, 1), deg[e.source] + deg[e.target]), reverse=True)[:max_edges]

        labels = {n.id: n.label for n in nodes}
        relations = sorted({e.relation for e in edges})
        planes = sorted({n.plane for n in nodes})
        types = sorted({n.type for n in nodes})
        return {
            "schema_version": "bunya-jido-v1",
            "generated_at": now_iso(),
            "title": f"Bunya-Jido · {self.project_name}",
            "description": "Single-file interactive graph generated from repository files, imports, docs, config, and runtime artifacts.",
            "artifact_mode": "static_scan",
            "grounding": {
                "status": "not_assessed",
                "publishable": False,
                "draft_override": False,
                "publish_blockers": [],
                "warnings": [],
                "metrics": {},
            },
            "stats": {"nodes": len(nodes), "edges": len(edges), "relations": relations, "planes": planes, "types": types},
            "nodes": [n.to_json() for n in sorted(nodes, key=lambda n: (n.plane, n.type, n.label.lower()))],
            "edges": [e.to_json(labels) for e in edges],
            "path_presets": self._path_presets(nodes, edges),
            "source_documents": [],
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def _path_presets(self, nodes: list[Node], edges: list[Edge]) -> list[dict[str, Any]]:
        by_plane = defaultdict(list)
        for n in nodes:
            by_plane[n.plane].append(n)
        def top_ids(planes: Iterable[str], limit: int = 24) -> list[str]:
            arr = [n for p in planes for n in by_plane.get(p, [])]
            arr = sorted(arr, key=lambda n: (n.major, n.degree, n.size), reverse=True)[:limit]
            return [n.id for n in arr]
        presets = [
            {"id": "overview", "label": "Project Overview", "description": "Root, packages, entrypoints, config, and high-degree nodes.", "node_ids": top_ids(["repo", "config", "code"], 32)},
            {"id": "code_flow", "label": "Code Flow", "description": "Python/JS modules, definitions, imports, and calls.", "node_ids": top_ids(["code", "external"], 36)},
            {"id": "docs_config", "label": "Docs + Config", "description": "Markdown docs and configuration files.", "node_ids": top_ids(["docs", "config", "repo"], 30)},
            {"id": "runtime_artifacts", "label": "Runtime Artifacts", "description": "Logs, state files, outputs, data, and generated artifacts.", "node_ids": top_ids(["runtime", "data"], 30)},
            {"id": "api_routes", "label": "API / Model Routes", "description": "Detected API providers, model-server hints, and files that call them.", "node_ids": top_ids(["external", "config", "code"], 34)},
            {"id": "tests", "label": "Tests", "description": "Test files and modules they appear to exercise.", "node_ids": top_ids(["tests", "code"], 30)},
        ]
        # Add labels for compatibility with older viewer path cards.
        id_to_label = {n.id: n.label for n in nodes}
        for p in presets:
            p["nodes"] = [id_to_label.get(i, i) for i in p["node_ids"]]
        return presets


def iter_repo_files(root: Path, max_files: int = 5000, include_hidden: bool = False, data_policy: str = "summary") -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and (include_hidden or not d.startswith("."))]
        if data_policy == "summary":
            # Dataset directories can contain thousands or millions of files.
            # Keep the directory-level node, but do not walk individual dataset items by default.
            dirnames[:] = [d for d in dirnames if d.lower() not in HEAVY_DATA_DIR_HINTS]
        for name in filenames:
            if name.endswith((".pyc", ".pyo", ".so", ".dll", ".dylib", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".tar", ".gz", ".7z")):
                continue
            p = dpath / name
            try:
                if p.stat().st_size > 3_000_000:
                    continue
            except Exception:
                continue
            files.append(p)
            if len(files) >= max_files:
                return files
    return files


def classify_path(rel: str, suffix: str) -> tuple[str, str]:
    parts = rel.split("/")
    lowered = [p.lower() for p in parts]
    if any(p in TEST_DIR_HINTS for p in lowered) or Path(rel).name.startswith("test_") or Path(rel).name.endswith("_test.py"):
        return "test", "tests"
    if any(p in DOC_DIR_HINTS for p in lowered) or suffix in {".md", ".rst"}:
        return "document", "docs"
    if any(p in RUNTIME_DIR_HINTS for p in lowered) or suffix in {".log", ".jsonl"}:
        return "runtime", "runtime"
    if any(p in DATA_DIR_HINTS for p in lowered) or suffix in {".csv", ".tsv", ".parquet", ".npy", ".npz", ".ipynb"}:
        return "data", "data"
    return "module", "code"


def module_name_from_path(root: Path, path: Path) -> str:
    rel = path.resolve().relative_to(root).with_suffix("").as_posix()
    if rel.startswith("src/"):
        rel = rel[4:]
    return rel.replace("/", ".")


def first_component(name: str) -> str:
    return name.split(".")[0] if name else ""


def infer_project_name(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and tomllib:
        try:
            data = tomllib.loads(read_text(pyproject, 150_000))
            name = data.get("project", {}).get("name") or data.get("tool", {}).get("poetry", {}).get("name")
            if name:
                return str(name)
        except Exception:
            pass
    package_json = root / "package.json"
    if package_json.exists():
        try:
            data = json.loads(read_text(package_json, 150_000))
            if data.get("name"):
                return str(data["name"]).split("/")[-1]
        except Exception:
            pass
    return root.name


class RepoScanner:
    def __init__(self, root: Path, mode: str = "auto", max_files: int = 5000, max_nodes: int = 700, max_edges: int = 1800, include_hidden: bool = False, show_root: bool = False, data_policy: str = "summary", max_data_files: int = 25) -> None:
        self.root = root.resolve()
        self.mode = mode
        self.max_files = max_files
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.include_hidden = include_hidden
        self.show_root = show_root
        self.data_policy = data_policy
        self.max_data_files = max_data_files
        self.project_name = infer_project_name(self.root)
        self.g = GraphBuilder(self.root, self.project_name)
        self.files: list[Path] = []
        self.py_files: list[Path] = []
        self.js_files: list[Path] = []
        self.md_files: list[Path] = []
        self.config_files: list[Path] = []
        self.runtime_files: list[Path] = []
        self.data_files: list[Path] = []
        self.internal_modules: set[str] = set()
        self.internal_first_components: set[str] = set()

    def scan(self) -> dict[str, Any]:
        self.files = iter_repo_files(self.root, self.max_files, include_hidden=self.include_hidden, data_policy=self.data_policy)
        self._partition_files()
        self._scan_top_dirs()
        self._scan_config()
        if self.mode in {"auto", "python", "all"}:
            self._scan_python()
        if self.mode in {"auto", "all"}:
            self._scan_js_ts()
        if self.mode in {"auto", "docs", "all"}:
            self._scan_markdown()
        if self.mode in {"auto", "runtime", "all"}:
            self._scan_runtime_and_data()
        self._scan_api_hints_global()
        return self.g.finish(max_nodes=self.max_nodes, max_edges=self.max_edges, show_root=self.show_root)

    def _partition_files(self) -> None:
        for p in self.files:
            rel = self.g.relpath(p)
            suffix = p.suffix.lower()
            name = p.name
            if suffix == ".py":
                self.py_files.append(p)
                self.internal_modules.add(module_name_from_path(self.root, p))
            elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
                self.js_files.append(p)
            elif suffix in {".md", ".rst"}:
                self.md_files.append(p)
            if name in CONFIG_FILES or any(part == ".github" for part in rel.split("/")):
                self.config_files.append(p)
            kind, plane = classify_path(rel, suffix)
            if kind == "runtime":
                self.runtime_files.append(p)
            elif kind == "data":
                self.data_files.append(p)
        self.internal_first_components = {first_component(m) for m in self.internal_modules}

    def _scan_top_dirs(self) -> None:
        for child in sorted(self.root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir() or child.name in IGNORE_DIRS or child.name.startswith("."):
                continue
            rel = child.name
            lname = rel.lower()
            if lname in TEST_DIR_HINTS:
                type_, plane = "directory", "tests"
            elif lname in DOC_DIR_HINTS:
                type_, plane = "directory", "docs"
            elif lname in RUNTIME_DIR_HINTS:
                type_, plane = "directory", "runtime"
            elif lname in DATA_DIR_HINTS:
                type_, plane = "directory", "data"
            elif lname in SRC_DIR_HINTS or (child / "__init__.py").exists():
                type_, plane = "package", "repo"
            else:
                type_, plane = "directory", "repo"
            desc = ""
            if lname in HEAVY_DATA_DIR_HINTS and self.data_policy == "summary":
                desc = "Dataset directory summarized by Bunya-Jido; individual files are omitted by default."
            nid = self.g.add_node(f"dir:{rel}", rel, type_, plane, source_path=rel, major=(type_ == "package"), description=desc)
            self.g.add_edge(self.g.root_id, nid, "contains", "structure", evidence={"kind": "directory", "path": rel})

    def _scan_config(self) -> None:
        for p in sorted(set(self.config_files), key=lambda p: self.g.relpath(p))[:90]:
            rel = self.g.relpath(p)
            n = self.g.add_file_node(p, "config", "config", major=p.name in {"pyproject.toml", "package.json", "README.md"})
            self.g.add_edge(self.g.root_id, n, "contains", "config", evidence={"kind": "config_file", "path": rel})
            if p.name == "pyproject.toml":
                self._parse_pyproject(p, n)
            elif p.name == "package.json":
                self._parse_package_json(p, n)
            elif p.name.startswith("requirements"):
                self._parse_requirements(p, n)

    def _external_dep_node(self, name: str, source_path: str = "") -> str:
        name = re.sub(r"[^A-Za-z0-9_.-]+", "", name).strip("._-")
        if not name:
            return ""
        return self.g.add_node(f"external:{name.lower()}", name, "external", "external", source_path=source_path, description="External dependency or imported package.")

    def _api_node(self, label: str, tag: str) -> str:
        return self.g.add_node(f"api:{slug(label)}", label, "api_provider", "external", tags=[f"api/{tag.lower()}"], description="Detected API, model server, or hosted service hint.", major=True, size=18)

    def _parse_pyproject(self, p: Path, config_node: str) -> None:
        if not tomllib:
            return
        try:
            data = tomllib.loads(read_text(p, 300_000))
        except Exception:
            return
        project = data.get("project", {}) or {}
        deps = list(project.get("dependencies", []) or [])
        optional = project.get("optional-dependencies", {}) or {}
        for v in optional.values():
            deps.extend(v or [])
        for dep in deps[:80]:
            m = re.match(r"\s*([A-Za-z0-9_.-]+)", str(dep))
            if m:
                dnode = self._external_dep_node(m.group(1), self.g.relpath(p))
                if dnode:
                    self.g.add_edge(config_node, dnode, "uses_module", "dependency", note="declared dependency", evidence={"kind": "pyproject_dependency", "path": self.g.relpath(p)})
        scripts = project.get("scripts", {}) or {}
        for name, target in list(scripts.items())[:50]:
            snode = self.g.add_node(f"entrypoint:{name}", str(name), "entrypoint", "code", source_path=self.g.relpath(p), description=str(target), major=True, size=17)
            self.g.add_edge(config_node, snode, "defines", "entrypoint", evidence={"kind": "pyproject_script", "path": self.g.relpath(p)})
            mod = str(target).split(":", 1)[0]
            if mod:
                mnode = self.g.add_node(f"module:{mod}", mod, "module", "code", source_path="", description="Entrypoint target module inferred from pyproject.toml.")
                self.g.module_to_node.setdefault(mod, mnode)
                self.g.add_edge(snode, mnode, "calls", "entrypoint", evidence={"kind": "pyproject_script_target", "path": self.g.relpath(p), "target": str(target)})

    def _parse_package_json(self, p: Path, config_node: str) -> None:
        try:
            data = json.loads(read_text(p, 300_000))
        except Exception:
            return
        for group in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            deps = data.get(group, {}) or {}
            for name in list(deps)[:100]:
                dnode = self._external_dep_node(name, self.g.relpath(p))
                if dnode:
                    self.g.add_edge(config_node, dnode, "uses_module", "dependency", note=group, evidence={"kind": "package_json_dependency", "path": self.g.relpath(p)})
        for name, script in list((data.get("scripts", {}) or {}).items())[:60]:
            snode = self.g.add_node(f"entrypoint:npm:{name}", f"npm:{name}", "entrypoint", "code", source_path=self.g.relpath(p), description=str(script), major=name in {"start", "build", "test", "dev"})
            self.g.add_edge(config_node, snode, "defines", "entrypoint", evidence={"kind": "package_json_script", "path": self.g.relpath(p)})

    def _parse_requirements(self, p: Path, config_node: str) -> None:
        for line in read_text(p, 200_000).splitlines()[:500]:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            m = re.match(r"([A-Za-z0-9_.-]+)", line)
            if m:
                dnode = self._external_dep_node(m.group(1), self.g.relpath(p))
                if dnode:
                    self.g.add_edge(config_node, dnode, "uses_module", "dependency", evidence={"kind": "requirements", "path": self.g.relpath(p)})

    def _scan_python(self) -> None:
        module_nodes: dict[Path, str] = {}
        local_defs_by_path: dict[Path, dict[str, str]] = {}
        for p in sorted(self.py_files, key=lambda p: self.g.relpath(p))[:900]:
            rel = self.g.relpath(p)
            type_, plane = classify_path(rel, ".py")
            if type_ == "test":
                ntype, nplane = "test", "tests"
            else:
                ntype, nplane = "module", "code"
            modname = module_name_from_path(self.root, p)
            label = modname if len(modname) <= 44 else p.name
            if ntype == "module":
                node = self.g.add_node(f"module:{modname}", label, "module", "code", source_path=rel, major=(p.name in {"cli.py", "main.py", "app.py", "server.py", "manage.py"}))
                self.g.path_to_node[rel] = node
            else:
                node = self.g.add_file_node(p, ntype, nplane, label=label, major=(p.name in {"cli.py", "main.py", "app.py", "server.py", "manage.py"}))
            module_nodes[p] = node
            self.g.module_to_node[modname] = node
            # Attach to package/directory if known
            parts = rel.split("/")
            if len(parts) > 1:
                parent_dir = parts[0]
                dnode = self.g.nodes.get(slug(f"dir:{parent_dir}"))
                if dnode:
                    self.g.add_edge(dnode.id, node, "contains", "structure", evidence={"kind": "file", "path": rel})
            else:
                self.g.add_edge(self.g.root_id, node, "contains", "structure", evidence={"kind": "file", "path": rel})
            text = read_text(p)
            try:
                tree = ast.parse(text, filename=rel)
            except SyntaxError:
                continue
            # imports
            for item in ast.walk(tree):
                if isinstance(item, ast.Import):
                    for alias in item.names:
                        self._add_import_edge(node, alias.name, rel, getattr(item, "lineno", None))
                elif isinstance(item, ast.ImportFrom):
                    if item.module:
                        self._add_import_edge(node, item.module, rel, getattr(item, "lineno", None))
            # definitions
            local_defs: dict[str, str] = {}
            for item in tree.body:
                if isinstance(item, ast.ClassDef):
                    cid = self.g.add_node(f"class:{rel}:{item.name}", item.name, "class", "code", source_path=f"{rel}:{item.lineno}", description=f"Class defined in {rel}", size=9)
                    self.g.add_edge(node, cid, "defines", "code", evidence={"kind": "python_class", "path": rel, "line": item.lineno})
                    local_defs[item.name] = cid
                    self.g.defined_symbols[item.name].append(cid)
                elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fid = self.g.add_node(f"function:{rel}:{item.name}", item.name, "function", "code", source_path=f"{rel}:{item.lineno}", description=f"Function defined in {rel}", major=item.name in {"main", "app", "run", "build", "cli"}, size=9)
                    self.g.add_edge(node, fid, "defines", "code", evidence={"kind": "python_function", "path": rel, "line": item.lineno})
                    local_defs[item.name] = fid
                    self.g.defined_symbols[item.name].append(fid)
            local_defs_by_path[p] = local_defs
            # local calls and API env hints
            call_counts: Counter[str] = Counter()
            for item in ast.walk(tree):
                if isinstance(item, ast.Call):
                    name = self._call_name(item.func)
                    if name:
                        call_counts[name] += 1
            for name, count in call_counts.most_common(35):
                simple = name.split(".")[-1]
                if simple in local_defs:
                    self.g.add_edge(node, local_defs[simple], "calls", "call", note=f"{count} observed call(s)", evidence={"kind": "python_ast_call", "path": rel})
            self._scan_text_for_api_edges(text, node, rel)
        # Link tests to likely modules by name
        mod_by_base = {Path(p).stem.replace("test_", "").replace("_test", ""): node for p, node in module_nodes.items() if self.g.nodes[node].type == "module"}
        for p, node in module_nodes.items():
            if self.g.nodes[node].type == "test":
                base = p.stem.replace("test_", "").replace("_test", "")
                if base in mod_by_base:
                    self.g.add_edge(node, mod_by_base[base], "tested_by", "test", confidence="inferred", evidence={"kind": "filename_match", "path": self.g.relpath(p)})

    def _add_import_edge(self, source_node: str, import_name: str, rel: str, line: int | None = None) -> None:
        first = first_component(import_name)
        if not first:
            return
        if first in STDLIB_MODULES:
            return
        evidence = {"kind": "python_import", "path": rel}
        if line:
            evidence["line"] = line
        # API lane detection first
        lowered = import_name.lower()
        for hint, (label, tag) in API_HINTS.items():
            if lowered.startswith(hint) or first.lower() == hint:
                api = self._api_node(label, tag)
                self.g.add_edge(source_node, api, "api_calls", "api", evidence=evidence)
                return
        if first in self.internal_first_components:
            # Edge to best known internal module if available, otherwise package node.
            target = self.g.module_to_node.get(import_name)
            if not target:
                target = self.g.add_node(f"package:{first}", first, "package", "repo", description="Internal package inferred from imports.", major=True)
            self.g.add_edge(source_node, target, "uses_module", "import", evidence=evidence)
        else:
            ext = self._external_dep_node(first, rel)
            if ext:
                self.g.add_edge(source_node, ext, "uses_module", "dependency", evidence=evidence)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = self._call_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""

    def _scan_js_ts(self) -> None:
        import_re = re.compile(r"(?:from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")
        class_re = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)")
        function_re = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)|const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")
        for p in sorted(self.js_files, key=lambda p: self.g.relpath(p))[:650]:
            rel = self.g.relpath(p)
            kind, plane = classify_path(rel, p.suffix.lower())
            ntype = "test" if kind == "test" else "module"
            nplane = "tests" if ntype == "test" else "code"
            node = self.g.add_file_node(p, ntype, nplane, major=p.name in {"index.ts", "index.js", "server.ts", "server.js", "main.ts", "main.js"})
            text = read_text(p)
            for m in import_re.finditer(text):
                name = m.group(1) or m.group(2) or ""
                if name.startswith("."):
                    self.g.add_edge(node, self.g.root_id, "uses_module", "import", confidence="inferred", evidence={"kind": "js_relative_import", "path": rel})
                else:
                    first = name.split("/")[0] if not name.startswith("@") else "/".join(name.split("/")[:2])
                    api_added = False
                    for hint, (label, tag) in API_HINTS.items():
                        if hint in first.lower():
                            api = self._api_node(label, tag)
                            self.g.add_edge(node, api, "api_calls", "api", evidence={"kind": "js_import", "path": rel})
                            api_added = True
                            break
                    if not api_added:
                        ext = self._external_dep_node(first, rel)
                        if ext:
                            self.g.add_edge(node, ext, "uses_module", "dependency", evidence={"kind": "js_import", "path": rel})
            for m in class_re.finditer(text[:250_000]):
                cname = m.group(1)
                cid = self.g.add_node(f"class:{rel}:{cname}", cname, "class", "code", source_path=rel, size=8)
                self.g.add_edge(node, cid, "defines", "code", evidence={"kind": "js_class", "path": rel})
            count = 0
            for m in function_re.finditer(text[:250_000]):
                fname = m.group(1) or m.group(2)
                if not fname:
                    continue
                fid = self.g.add_node(f"function:{rel}:{fname}", fname, "function", "code", source_path=rel, size=8)
                self.g.add_edge(node, fid, "defines", "code", evidence={"kind": "js_function", "path": rel})
                count += 1
                if count > 10:
                    break
            self._scan_text_for_api_edges(text, node, rel)

    def _scan_markdown(self) -> None:
        md_nodes: dict[str, str] = {}
        for p in sorted(self.md_files, key=lambda p: self.g.relpath(p))[:260]:
            rel = self.g.relpath(p)
            text = read_text(p, 300_000)
            title = p.stem
            m = re.search(r"^#\s+(.+)$", text, flags=re.M)
            if m:
                title = m.group(1).strip()[:80]
            node = self.g.add_file_node(p, "document", "docs", label=title, major=p.name.lower().startswith("readme"))
            md_nodes[rel] = node
            if p.name.lower().startswith("readme") or len(rel.split("/")) == 1:
                self.g.add_edge(self.g.root_id, node, "documents", "docs", evidence={"kind": "markdown", "path": rel})
        # Links after all md nodes are known
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)|\[\[([^\]]+)\]\]")
        for p in sorted(self.md_files, key=lambda p: self.g.relpath(p))[:260]:
            rel = self.g.relpath(p)
            source = md_nodes.get(rel)
            if not source:
                continue
            text = read_text(p, 300_000)
            seen = set()
            for m in link_re.finditer(text):
                raw = (m.group(1) or m.group(2) or "").split("#", 1)[0].strip()
                if not raw or raw.startswith(("http://", "https://", "mailto:")):
                    continue
                raw = raw.replace("\\", "/")
                if not raw.endswith((".md", ".rst")) and m.group(2):
                    raw += ".md"
                candidate = (p.parent / raw).resolve()
                try:
                    target_rel = candidate.relative_to(self.root).as_posix()
                except Exception:
                    target_rel = raw.lstrip("/")
                target = md_nodes.get(target_rel)
                if target and target not in seen:
                    seen.add(target)
                    self.g.add_edge(source, target, "documents", "docs", evidence={"kind": "markdown_link", "path": rel})

    def _scan_runtime_and_data(self) -> None:
        for p in sorted(set(self.runtime_files), key=lambda p: self.g.relpath(p))[:160]:
            rel = self.g.relpath(p)
            node = self.g.add_file_node(p, "runtime", "runtime", major=p.name in {"workflow_trace.jsonl", "status.json", "events.jsonl"})
            parent_dir = f"dir:{rel.split('/')[0]}" if '/' in rel else ""
            parent = slug(parent_dir, 120) if parent_dir else self.g.root_id
            if parent not in self.g.nodes:
                parent = self.g.root_id
            self.g.add_edge(parent, node, "contains", "runtime", evidence={"kind": "runtime_artifact", "path": rel})
            if p.suffix.lower() == ".jsonl":
                self._scan_jsonl_events(p, node)
            elif p.suffix.lower() == ".json":
                self._scan_json_keys(p, node)
        data_limit = len(self.data_files) if self.data_policy == "full" else self.max_data_files
        if self.data_policy == "summary":
            data_limit = 0
        for p in sorted(set(self.data_files), key=lambda p: self.g.relpath(p))[:data_limit]:
            rel = self.g.relpath(p)
            node = self.g.add_file_node(p, "data", "data")
            parent_dir = f"dir:{rel.split('/')[0]}" if '/' in rel else ""
            parent = slug(parent_dir, 120) if parent_dir else self.g.root_id
            if parent not in self.g.nodes:
                parent = self.g.root_id
            self.g.add_edge(parent, node, "contains", "data", evidence={"kind": "data_file", "path": rel})

    def _scan_jsonl_events(self, p: Path, source: str) -> None:
        counts: Counter[str] = Counter()
        for line in read_text(p, 600_000).splitlines()[:500]:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            ev = obj.get("event") or obj.get("type") or obj.get("name") or obj.get("status")
            if ev:
                counts[str(ev)[:80]] += 1
        for ev, count in counts.most_common(25):
            enode = self.g.add_node(f"event:{self.g.relpath(p)}:{ev}", ev, "runtime", "runtime", source_path=self.g.relpath(p), description=f"Observed {count} time(s) in {p.name}")
            self.g.add_edge(source, enode, "emits", "runtime", evidence={"kind": "jsonl_event", "path": self.g.relpath(p), "count": count})

    def _scan_json_keys(self, p: Path, source: str) -> None:
        try:
            obj = json.loads(read_text(p, 600_000))
        except Exception:
            return
        if isinstance(obj, dict):
            interesting = [k for k in obj.keys() if str(k).lower() in {"status", "state", "event", "type", "name", "version", "model", "provider"}]
            for k in interesting[:8]:
                label = f"{k}: {str(obj.get(k))[:48]}"
                knode = self.g.add_node(f"runtime-key:{self.g.relpath(p)}:{k}", label, "runtime", "runtime", source_path=self.g.relpath(p))
                self.g.add_edge(source, knode, "records", "runtime", evidence={"kind": "json_key", "path": self.g.relpath(p), "key": k})

    def _scan_api_hints_global(self) -> None:
        # Config/env-like files and all text-ish files with API key/base markers.
        candidates = list(dict.fromkeys(self.config_files + self.py_files[:250] + self.js_files[:250]))
        for p in candidates[:500]:
            rel = self.g.relpath(p)
            text = read_text(p, 250_000)
            source = self.g.path_to_node.get(rel)
            if not source:
                continue
            self._scan_text_for_api_edges(text, source, rel)

    def _scan_text_for_api_edges(self, text: str, source_node: str, rel: str) -> None:
        lowered = text.lower()
        env_patterns = {
            "OPENAI": "External OpenAI API", "ANTHROPIC": "External Anthropic API", "GEMINI": "External Gemini API",
            "GOOGLE_API": "External Gemini API", "QWEN": "Local Qwen / Model Server", "OLLAMA": "Local Ollama / Model Server",
            "VLLM": "Local vLLM Server", "HF_TOKEN": "Hugging Face Hub", "HUGGINGFACE": "Hugging Face Hub",
            "MISTRAL": "External Mistral API", "GROQ": "External Groq API", "COHERE": "External Cohere API",
            "BEDROCK": "AWS / Bedrock API", "AZURE_OPENAI": "Azure API",
        }
        for token, label in env_patterns.items():
            if token.lower() in lowered:
                api = self._api_node(label, token)
                self.g.add_edge(source_node, api, "api_calls", "api", confidence="inferred", evidence={"kind": "api_text_hint", "path": rel, "token": token})


def build_graph(root: str | Path, mode: str = "auto", max_files: int = 5000, max_nodes: int = 700, max_edges: int = 1800, include_hidden: bool = False, show_root: bool = False, data_policy: str = "summary", max_data_files: int = 25) -> dict[str, Any]:
    root_path = Path(root).resolve()
    if not root_path.exists() or not root_path.is_dir():
        raise FileNotFoundError(f"root does not exist or is not a directory: {root_path}")
    mode = {"full":"all", "code":"python", "external":"auto"}.get(mode, mode)
    scanner = RepoScanner(root_path, mode=mode, max_files=max_files, max_nodes=max_nodes, max_edges=max_edges, include_hidden=include_hidden, show_root=show_root, data_policy=data_policy, max_data_files=max_data_files)
    return scanner.scan()
