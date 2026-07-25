# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Make the tools importable by name from a submodule checkout.

The tools are standalone scripts rather than an installed package, so the directory
holding them goes on the path before the tests import them.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
