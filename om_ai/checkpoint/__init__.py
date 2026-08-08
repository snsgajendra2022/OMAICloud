"""OM AI checkpoint bundle package.

Exports
-------
CheckpointBundle  – dataclass holding all bundle metadata and loaded states
save_bundle       – serialise model + metadata into a standardised directory layout
load_bundle       – deserialise a bundle directory back into a CheckpointBundle
verify_integrity  – validate SHA256 checksums for all bundle files
"""

from om_ai.checkpoint.bundle import (
    CheckpointBundle,
    load_bundle,
    save_bundle,
    verify_integrity,
)

__all__ = [
    "CheckpointBundle",
    "save_bundle",
    "load_bundle",
    "verify_integrity",
]
