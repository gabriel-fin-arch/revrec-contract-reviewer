"""Shared fixtures.

The corpus is built once per session into a temporary directory rather than
read from the repository. Tests then can't be quietly passing because someone
edited a PDF by hand, and a fresh checkout with no corpus/ still runs them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from revrec_contract_reviewer.corpus import generate_corpus
from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.segment import segmented


@pytest.fixture(scope="session")
def corpus_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("corpus")
    generate_corpus(target)
    return target


@pytest.fixture(scope="session")
def documents(corpus_dir: Path) -> dict[str, ContractDocument]:
    return {path.stem: segmented(load_contract(path)) for path in sorted(corpus_dir.glob("*.pdf"))}


@pytest.fixture
def helix(documents: dict[str, ContractDocument]) -> ContractDocument:
    return documents["nimbus-of-helix"]


@pytest.fixture
def calderwood_order(documents: dict[str, ContractDocument]) -> ContractDocument:
    return documents["nimbus-of-calderwood-2025"]


@pytest.fixture
def vantage(documents: dict[str, ContractDocument]) -> ContractDocument:
    return documents["nimbus-msa-vantage"]


@pytest.fixture
def pinegrove(documents: dict[str, ContractDocument]) -> ContractDocument:
    return documents["nimbus-of-pinegrove"]
