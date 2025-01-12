from __future__ import annotations

from pathlib import Path

# File where to write DHCORE_ACCESS_TOKEN and DHCORE_REFRESH_TOKEN
# It's used because we inject the variables in jupyter env,
# but refresh token is only available once. Is it's used, we cannot
# overwrite it with coder, so we need to store the new one in a file,
# preserved for jupyter restart
ENV_FILE = Path.home() / ".dhcore.ini"


# API levels that are supported
MAX_API_LEVEL = 20
MIN_API_LEVEL = 9
LIB_VERSION = 9
