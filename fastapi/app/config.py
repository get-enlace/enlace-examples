"""Runtime configuration for this example — a single `Settings` value, read
once from the environment. Plays the same role `process.env.PORT` plays
directly in the express/nest examples here; pulled into its own module
instead of inlined, since `main.py` and `errors.py` both need it and a real
service would likely grow more settings than just this one.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    port: int = int(os.environ.get("PORT", "4000"))


settings = Settings()
