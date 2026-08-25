"""Approved open training-data catalog for OM AI (license-first).

These are *sources* you may legally collect into OMAI-Corpus-v1 after
review. OM never pretends trillions of tokens already exist in-repo.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# Licenses we allow into the training corpus by default.
ALLOWED_TRAINING_LICENSES = {
    "odc-by",
    "cc-by-sa",
    "cc-by",
    "cc0",
    "public-domain",
    "project-owned",
    "proprietary-owned",
    "apache-2.0",
    "mit",
    "bsd-2-clause",
    "bsd-3-clause",
}


@dataclass(frozen=True)
class CatalogSource:
    source_id: str
    name: str
    homepage: str
    license: str
    owner: str
    category: str
    language: str
    allowed_for_training: bool
    fetch_method: str  # wikipedia_api | gutenberg_http | hf_datasets | manual | local
    notes: str
    typical_use: str
    scale_hint: str


CATALOG: list[CatalogSource] = [
    CatalogSource(
        source_id="fineweb",
        name="FineWeb",
        homepage="https://huggingface.co/datasets/HuggingFaceFW/fineweb",
        license="odc-by",
        owner="HuggingFaceFW",
        category="web",
        language="en",
        allowed_for_training=True,
        fetch_method="hf_datasets",
        notes="Cleaned/deduped web text. Use streaming + max_docs for local samples.",
        typical_use="1B→70B general pretrain mix",
        scale_hint="TB-class when fully downloaded",
    ),
    CatalogSource(
        source_id="common-crawl",
        name="Common Crawl",
        homepage="https://commoncrawl.org/",
        license="public-web-crawl",
        owner="Common Crawl Foundation",
        category="web",
        language="multi",
        allowed_for_training=False,  # requires license cleaning before train
        fetch_method="manual",
        notes="Raw crawl is NOT auto-approved. Filter + license clean first, then re-mark allowed.",
        typical_use="web scale after governance pass",
        scale_hint="petabytes raw",
    ),
    CatalogSource(
        source_id="wikipedia-en",
        name="English Wikipedia",
        homepage="https://dumps.wikimedia.org/",
        license="cc-by-sa",
        owner="Wikimedia Foundation",
        category="knowledge",
        language="en",
        allowed_for_training=True,
        fetch_method="wikipedia_api",
        notes="CC BY-SA — keep attribution. Sample via API; full dumps via dumps.wikimedia.org.",
        typical_use="knowledge / factuality",
        scale_hint="~100GB+ full dump",
    ),
    CatalogSource(
        source_id="gutenberg",
        name="Project Gutenberg",
        homepage="https://www.gutenberg.org/",
        license="public-domain",
        owner="Project Gutenberg",
        category="books",
        language="en",
        allowed_for_training=True,
        fetch_method="gutenberg_http",
        notes="Public-domain books only. Respect Gutenberg terms of use for bulk access.",
        typical_use="language / writing style",
        scale_hint="70k+ books",
    ),
    CatalogSource(
        source_id="arxiv",
        name="arXiv bulk",
        homepage="https://arxiv.org/help/bulk_data",
        license="mixed-arxiv",
        owner="arXiv",
        category="science",
        language="en",
        allowed_for_training=False,  # license varies per paper
        fetch_method="manual",
        notes="License varies per paper. Only import papers with clear training-safe terms.",
        typical_use="scientific reasoning",
        scale_hint="large; selective import",
    ),
    CatalogSource(
        source_id="the-stack",
        name="The Stack",
        homepage="https://huggingface.co/datasets/bigcode/the-stack",
        license="mixed-permissive",
        owner="BigCode",
        category="code",
        language="code",
        allowed_for_training=False,  # must filter GPL / secrets
        fetch_method="hf_datasets",
        notes="Filter out copyleft / secrets / private code before allowing training.",
        typical_use="coding ability",
        scale_hint="TB-class",
    ),
    CatalogSource(
        source_id="open-assistant",
        name="OpenAssistant",
        homepage="https://huggingface.co/OpenAssistant",
        license="apache-2.0",
        owner="OpenAssistant",
        category="instruction",
        language="multi",
        allowed_for_training=True,
        fetch_method="hf_datasets",
        notes="Instruction / conversation data. Verify exact dataset license before commercial use.",
        typical_use="SFT / chat style",
        scale_hint="GB-class",
    ),
    CatalogSource(
        source_id="om-owned",
        name="OM owned / company data",
        homepage="local://om-owned",
        license="proprietary-owned",
        owner="OM AI",
        category="domain",
        language="multi",
        allowed_for_training=True,
        fetch_method="local",
        notes="Your docs, APIs, projects. Highest-value domain data.",
        typical_use="domain adaptation",
        scale_hint="your volume",
    ),
]


def catalog_as_dicts(*, training_only: bool = False) -> list[dict[str, Any]]:
    rows = []
    for s in CATALOG:
        if training_only and not s.allowed_for_training:
            continue
        d = asdict(s)
        d["license_ok_for_default_train"] = (
            s.allowed_for_training and s.license.lower() in ALLOWED_TRAINING_LICENSES
        )
        rows.append(d)
    return rows


def get_source(source_id: str) -> CatalogSource | None:
    sid = (source_id or "").strip().lower()
    for s in CATALOG:
        if s.source_id == sid:
            return s
    return None
