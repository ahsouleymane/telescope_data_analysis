r"""
Shared configuration for all scripts in code/.

BASE_DIR is the folder that holds the TeleScope dataset files (CSV) and where
results are written. Override it without editing any script:

    export TELESCOPE_DIR=/path/to/telescope_files      # Linux / macOS
    set TELESCOPE_DIR=C:\path\to\telescope_files        # Windows (cmd)

If TELESCOPE_DIR is not set, the previous default location is used, so
existing setups keep working unchanged.
"""

import os
from pathlib import Path

BASE_DIR = Path(
    os.environ.get(
        "TELESCOPE_DIR",
        Path.home() / "Documents" / "telescope_data_analysis" / "telescope_files",
    )
).expanduser()
