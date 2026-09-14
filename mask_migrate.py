"""doctor --migrate: convert a live-checkout machine and its consumers to taps through one recoverable journal.

RFC-MASK-0020 AC04; contracts/MIGRATION.md. Detection and the shared mapping live in ``mask_legacy``.
"""
from __future__ import annotations

import mask_core as c


def dispatch(args, output, home):
    c.fail('config.command_unavailable', 'doctor --migrate is not available in this build yet.')
