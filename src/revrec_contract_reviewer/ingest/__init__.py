"""PDF in, addressable text out."""

from revrec_contract_reviewer.ingest.pdf import load_contract
from revrec_contract_reviewer.ingest.text import NormalizedText

__all__ = ["NormalizedText", "load_contract"]
