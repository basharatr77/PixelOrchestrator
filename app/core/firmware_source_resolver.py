from dataclasses import dataclass
import re
from urllib.request import Request, urlopen


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


class GoogleFirmwareCandidateNormalizer:
    """Normalize Google firmware candidate metadata without verifying it."""

    _REQUIRED_FIELDS = (
        "source",
        "repository",
        "device_codename",
        "build_id",
        "android_release",
        "security_patch",
        "release_date",
        "package_url",
    )

    def normalize(self, candidate):
        candidate = candidate if isinstance(candidate, dict) else {}

        result = {
            field: candidate.get(field, "")
            for field in self._REQUIRED_FIELDS
        }

        package_sha256 = str(candidate.get("package_sha256", "")).strip()
        result["package_sha256"] = package_sha256 or "UNKNOWN"

        result["vbmeta_digest"] = (
            str(candidate.get("vbmeta_digest", "")).strip()
            or "UNKNOWN"
        )

        missing_required = any(
            not str(result[field]).strip()
            for field in self._REQUIRED_FIELDS
        )

        result["verification"] = "UNKNOWN"
        result["source_verified"] = False
        result["candidate_verified"] = False

        return result



class GoogleFirmwareSourceReader:
    """Read and classify official Google firmware source evidence.

    This reader does not download firmware or invent candidate metadata.
    """

    GOOGLE_FACTORY_IMAGES = "https://developers.google.com/android/images"
    GOOGLE_FULL_OTA = "https://developers.google.com/android/ota"

    def read_source(self, source_url):
        source_url = str(source_url or "").strip()

        if source_url == self.GOOGLE_FACTORY_IMAGES:
            return {
                "source": "GOOGLE",
                "repository": "FACTORY_IMAGES",
                "official_source": True,
                "evidence_reference": source_url,
                "verification": "UNKNOWN",
            }

        if source_url == self.GOOGLE_FULL_OTA:
            return {
                "source": "GOOGLE",
                "repository": "FULL_OTA",
                "official_source": True,
                "evidence_reference": source_url,
                "verification": "UNKNOWN",
            }

        return {
            "source": "UNKNOWN",
            "repository": "UNKNOWN",
            "official_source": False,
            "evidence_reference": source_url,
            "verification": "UNKNOWN",
        }

    def read_candidate(self, candidate):
        candidate = candidate if isinstance(candidate, dict) else {}

        result = {
            "source": candidate.get("source", "UNKNOWN"),
            "repository": candidate.get("repository", "UNKNOWN"),
            "device_codename": candidate.get("device_codename", "UNKNOWN"),
            "build_id": candidate.get("build_id", "UNKNOWN"),
            "android_release": candidate.get("android_release", "UNKNOWN"),
            "security_patch": candidate.get("security_patch", "UNKNOWN"),
            "release_date": candidate.get("release_date", "UNKNOWN"),
            "package_url": candidate.get("package_url", "UNKNOWN"),
            "package_sha256": candidate.get("package_sha256", "UNKNOWN"),
            "vbmeta_digest": candidate.get("vbmeta_digest", "UNKNOWN"),
            "source_verified": False,
            "candidate_verified": False,
            "verification": "UNKNOWN",
        }

        return result

    def fetch_source(self, source_url):
        source_url = str(source_url or "").strip()

        source = self.read_source(source_url)

        if not source["official_source"]:
            source["raw_source_evidence"] = ""
            return source

        try:
            request = Request(
                source_url,
                headers={"User-Agent": "PixelOrchestrator/1.0"},
            )
            with urlopen(request, timeout=15) as response:
                raw_source_evidence = response.read().decode(
                    "utf-8",
                    errors="replace",
                )
        except Exception:
            raw_source_evidence = ""

        source["raw_source_evidence"] = raw_source_evidence
        if not raw_source_evidence:
            source["verification"] = "UNKNOWN"

        return source

    def extract_candidates(self, source):
        if not isinstance(source, dict):
            return []

        if not source.get("official_source"):
            return []

        raw = str(source.get("raw_source_evidence", "") or "").strip()
        if not raw:
            return []

        fields = {
            "device_codename": r"device=([^\s]+)",
            "build_id": r"build=([^\s]+)",
            "android_release": r"android=([^\s]+)",
            "security_patch": r"security_patch=([^\s]+)",
            "release_date": r"release_date=([^\s]+)",
            "package_url": r"package_url=(https?://[^\s]+)",
        }

        candidate = {
            field: (re.search(pattern, raw) or [None, "UNKNOWN"])[1]
            for field, pattern in fields.items()
        }

        candidate["source"] = source.get("source", "UNKNOWN")
        candidate["repository"] = source.get("repository", "UNKNOWN")
        candidate["package_sha256"] = "UNKNOWN"
        candidate["vbmeta_digest"] = "UNKNOWN"
        candidate["source_verified"] = False
        candidate["candidate_verified"] = False
        candidate["verification"] = "UNKNOWN"

        return [candidate]



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

class FirmwareSourceAdapter:
    """Common contract for OEM firmware source adapters."""

    def identify_source(self, source_url):
        return {
            "source": "UNKNOWN",
            "repository": "UNKNOWN",
            "official_source": False,
            "evidence_reference": str(source_url or "").strip(),
            "verification": "UNKNOWN",
        }

    def fetch_candidates(self, source):
        return []

    def normalize_candidate(self, candidate):
        candidate = candidate if isinstance(candidate, dict) else {}

        fields = (
            "source",
            "repository",
            "device_codename",
            "build_id",
            "android_release",
            "security_patch",
            "release_date",
            "package_url",
        )

        result = {
            field: str(candidate.get(field, "")).strip() or "UNKNOWN"
            for field in fields
        }

        result["package_sha256"] = (
            str(candidate.get("package_sha256", "")).strip()
            or "UNKNOWN"
        )
        result["vbmeta_digest"] = (
            str(candidate.get("vbmeta_digest", "")).strip()
            or "UNKNOWN"
        )
        result["source_verified"] = False
        result["candidate_verified"] = False
        result["verification"] = "UNKNOWN"

        return result
