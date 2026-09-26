from dataclasses import dataclass


@dataclass(frozen=True)
class FirmwareCandidate:
    source: str
    repository: str
    device_codename: str
    build_id: str
    android_release: str
    security_patch: str
    release_date: str
    package_url: str
    package_sha256: str
    source_verified: bool
    candidate_verified: bool
    verification: str

class GoogleFirmwareSourceResolver:
    """Resolve official Google firmware source families.

    This resolver does not scrape, download, or select a firmware package.
    It only maps known Google Pixel device codenames to official source
    repositories. Exact package verification remains a later step.
    """

    GOOGLE_FACTORY_IMAGES = "https://developers.google.com/android/images"
    GOOGLE_FULL_OTA = "https://developers.google.com/android/ota"

    # Known Pixel codenames used only for source-family recognition.
    # This is deliberately not a firmware-version/package database.
    _PIXEL_CODENAMES = {
        "shiba",
        "husky",
        "akita",
        "komodo",
        "caiman",
        "comet",
        "tokay",
        "tegu",
    }

    def find_candidates(self, device_identity):
        if not isinstance(device_identity, dict):
            return {
                "source": "GOOGLE",
                "repository": "UNKNOWN",
                "availability": "NOT_VERIFIED",
                "candidates": [],
            }

        codename = str(
            device_identity.get("device_codename", "")
        ).strip().lower()

        if not codename or codename == "unknown":
            return {
                "source": "GOOGLE",
                "repository": "UNKNOWN",
                "availability": "NOT_VERIFIED",
                "candidates": [],
            }

        if codename not in self._PIXEL_CODENAMES:
            return {
                "source": "GOOGLE",
                "repository": "UNKNOWN",
                "availability": "NOT_VERIFIED",
                "candidates": [],
            }

        return {
            "source": "GOOGLE",
            "repository": "FACTORY_IMAGES",
            "availability": "OFFICIAL_SOURCE",
            "candidates": [
                {
                    "device_codename": codename,
                    "source_url": self.GOOGLE_FACTORY_IMAGES,
                    "candidate_verified": False,
                }
            ],
        }
