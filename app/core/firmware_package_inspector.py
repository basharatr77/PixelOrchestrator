from hashlib import sha256
from pathlib import Path
import zipfile


class FirmwarePackageInspector:
    def inspect(self, package_path):
        package_path = Path(package_path)

        package_hash = sha256(
            package_path.read_bytes()
        ).hexdigest()

        with zipfile.ZipFile(package_path) as archive:
            members = archive.namelist()

        is_factory_structure = (
            any(member.lower().endswith(".zip") for member in members)
            and "flash-all.bat" in members
            and "flash-all.sh" in members
        )

        return {
            "package_type": (
                "PIXEL_FACTORY_IMAGE"
                if is_factory_structure
                else "UNKNOWN"
            ),
            "package_sha256": package_hash,
            "members": members,
            "integrity": "UNKNOWN",
            "verification": "UNKNOWN",
        }
