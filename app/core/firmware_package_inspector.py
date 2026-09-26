from hashlib import sha256
from pathlib import Path
import io
import zipfile


class FirmwarePackageInspector:
    def inspect(self, package_path):
        package_path = Path(package_path)

        package_hash = sha256(
            package_path.read_bytes()
        ).hexdigest()

        with zipfile.ZipFile(package_path) as archive:
            members = archive.namelist()

            nested_images = [
                member
                for member in members
                if member.lower().startswith("image-")
                and member.lower().endswith(".zip")
            ]

            nested_image = (
                nested_images[0]
                if nested_images
                else None
            )

            image_members = []

            if nested_image is not None:
                nested_data = archive.read(nested_image)
                try:
                    with zipfile.ZipFile(io.BytesIO(nested_data)) as image:
                        image_members = image.namelist()
                except zipfile.BadZipFile:
                    image_members = []

        is_factory_structure = (
            nested_image is not None
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
            "nested_image": nested_image,
            "image_members": image_members,
            "integrity": "UNKNOWN",
            "verification": "UNKNOWN",
        }
