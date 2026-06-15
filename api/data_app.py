from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Flask

if TYPE_CHECKING:
    from extensions.ext_login import DataLoginManager


class DataApp(Flask):
    """Flask application type with DATA-specific extension attributes."""

    login_manager: DataLoginManager
