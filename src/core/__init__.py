"""
Faceless YouTube Automation Platform
Copyright © 2025 Project Contributors

This file is part of the Faceless YouTube Automation Platform.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

# Make core modules easily importable
from src.core.models import (
    Base,
    User,
    Video,
    Script,
    Asset,
    VideoAsset,
    Platform,
    Publish,
    Analytics,
    Configuration,
    Revenue,
    VideoStatus,
    AssetType,
    LicenseType,
    PlatformName,
    PublishStatus,
)

from src.core.database import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_db,
    check_db_connection,
)

__all__ = [
    # Models
    "Base",
    "User",
    "Video",
    "Script",
    "Asset",
    "VideoAsset",
    "Platform",
    "Publish",
    "Analytics",
    "Configuration",
    "Revenue",
    # Enums
    "VideoStatus",
    "AssetType",
    "LicenseType",
    "PlatformName",
    "PublishStatus",
    # Database
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
    "init_db",
    "check_db_connection",
]
