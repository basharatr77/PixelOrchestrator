from pathlib import Path
from hashlib import sha256
import io
import zipfile

class FirmwarePackageInspector:
    def inspect(self, package_path):
        package_path = Path(package_path)
        package_hash = sha256(package_path.read_bytes()).hexdigest()

        with zipfile.ZipFile(package_path) as archive:
            members = archive.namelist()

            nested_images = [
                member
                for member in members
                if member.lower().startswith("image-")
                and member.lower().endswith(".zip")
            ]

            nested_image = nested_images[0] if nested_images else None
            image_members = []
            build_identity = {
                "device_codename": "UNKNOWN",
                "build_id": "UNKNOWN",
                "android_release": "UNKNOWN",
                "security_patch": "UNKNOWN",
            }
            build_identity_source = "UNKNOWN"

            if nested_image is not None:
                nested_data = archive.read(nested_image)
                try:
                    with zipfile.ZipFile(io.BytesIO(nested_data)) as image:
                        image_members = image.namelist()

                        if "android-info.txt" in image_members:
                            metadata = image.read("android-info.txt").decode(
                                "utf-8",
                                errors="replace",
                            )

                            values = {}
                            for line in metadata.splitlines():
                                if "=" in line:
                                    key, value = line.split("=", 1)
                                    values[key.strip()] = value.strip()

                            build_identity = {
                                "device_codename": values.get(
                                    "board",
                                    "UNKNOWN",
                                ),
                                "build_id": values.get(
                                    "build_id",
                                    "UNKNOWN",
                                ),
                                "android_release": values.get(
                                    "android_version",
                                    "UNKNOWN",
                                ),
                                "security_patch": values.get(
                                    "security_patch",
                                    "UNKNOWN",
                                ),
                            }
                            build_identity_source = "android-info.txt"

                except zipfile.BadZipFile:
                    image_members = []

            image_evidence = {}
            for member in image_members:
                name = Path(member).name.lower()
                if name == "boot.img":
                    image_evidence[member] = "BOOT_IMAGE_PRESENT"
                elif name == "system.img":
                    image_evidence[member] = "SYSTEM_IMAGE_PRESENT"
                elif name == "vendor.img":
                    image_evidence[member] = "VENDOR_IMAGE_PRESENT"
                elif name == "vbmeta.img":
                    image_evidence[member] = "VBMETA_IMAGE_PRESENT"
                else:
                    image_evidence[member] = "UNKNOWN"

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
            "image_evidence": image_evidence,
            "build_identity": build_identity,
            "build_identity_source": build_identity_source,
            "integrity": "UNKNOWN",
            "verification": "UNKNOWN",
        }
