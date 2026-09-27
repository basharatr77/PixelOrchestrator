from hashlib import sha256
from pathlib import Path
import zipfile

from app.core.firmware_package_inspector import FirmwarePackageInspector
from app.core.firmware_compatibility import FirmwareCompatibilityChecker


def test_factory_package_inspection_extracts_verifiable_evidence(tmp_path):
    package = tmp_path / "a32-factory.zip"

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(
            "image-a32-test.zip",
            b"factory-image-payload",
        )
        archive.writestr(
            "flash-all.bat",
            b"@echo off",
        )
        archive.writestr(
            "flash-all.sh",
            b"#!/bin/sh",
        )

    result = FirmwarePackageInspector().inspect(package)

    assert result["package_type"] == "PIXEL_FACTORY_IMAGE"
    assert result["package_sha256"] == sha256(package.read_bytes()).hexdigest()
    assert result["members"] == [
        "image-a32-test.zip",
        "flash-all.bat",
        "flash-all.sh",
    ]
    assert result["integrity"] == "UNKNOWN"
    assert result["verification"] == "UNKNOWN"


def test_arbitrary_zip_is_not_verified_as_factory_image(tmp_path):
    package = tmp_path / "random.zip"

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("random.txt", b"not firmware")

    result = FirmwarePackageInspector().inspect(package)

    assert result["package_type"] == "UNKNOWN"
    assert result["verification"] == "UNKNOWN"

def test_factory_package_inspection_extracts_nested_image_evidence(tmp_path):
    package = tmp_path / "a32-factory.zip"

    image_zip = tmp_path / "image-a32-test.zip"
    with zipfile.ZipFile(image_zip, "w") as image:
        image.writestr("boot.img", b"boot")
        image.writestr("system.img", b"system")
        image.writestr("vendor.img", b"vendor")
        image.writestr("vbmeta.img", b"vbmeta")

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(
            "image-a32-test.zip",
            image_zip.read_bytes(),
        )
        archive.writestr("flash-all.bat", b"@echo off")
        archive.writestr("flash-all.sh", b"#!/bin/sh")

    result = FirmwarePackageInspector().inspect(package)

    assert result["nested_image"] == "image-a32-test.zip"
    assert result["image_members"] == [
        "boot.img",
        "system.img",
        "vendor.img",
        "vbmeta.img",
    ]

def test_factory_package_inspection_classifies_partition_image_evidence(tmp_path):
    package = tmp_path / "a32-factory.zip"

    image_zip = tmp_path / "image-a32-test.zip"
    with zipfile.ZipFile(image_zip, "w") as image:
        image.writestr("boot.img", b"boot")
        image.writestr("system.img", b"system")
        image.writestr("vendor.img", b"vendor")
        image.writestr("vbmeta.img", b"vbmeta")
        image.writestr("custom.img", b"unknown")

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("image-a32-test.zip", image_zip.read_bytes())
        archive.writestr("flash-all.bat", b"@echo off")
        archive.writestr("flash-all.sh", b"#!/bin/sh")

    result = FirmwarePackageInspector().inspect(package)

    assert result["image_evidence"] == {
        "boot.img": "BOOT_IMAGE_PRESENT",
        "system.img": "SYSTEM_IMAGE_PRESENT",
        "vendor.img": "VENDOR_IMAGE_PRESENT",
        "vbmeta.img": "VBMETA_IMAGE_PRESENT",
        "custom.img": "UNKNOWN",
    }

def test_factory_package_inspection_extracts_build_identity_evidence(tmp_path):
    package = tmp_path / "a32-factory.zip"

    image_zip = tmp_path / "image-a32-test.zip"
    with zipfile.ZipFile(image_zip, "w") as image:
        image.writestr(
            "android-info.txt",
            "\n".join(
                [
                    "board=a32",
                    "build_id=AQ3A.240829.003",
                    "android_version=15",
                    "security_patch=2024-09-01",
                ]
            ).encode(),
        )
        image.writestr("boot.img", b"boot")

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("image-a32-test.zip", image_zip.read_bytes())
        archive.writestr("flash-all.bat", b"@echo off")
        archive.writestr("flash-all.sh", b"#!/bin/sh")

    result = FirmwarePackageInspector().inspect(package)

    assert result["build_identity"] == {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    assert result["build_identity_source"] == "android-info.txt"

def test_factory_package_inspection_missing_build_metadata_is_unknown(tmp_path):
    package = tmp_path / "a32-factory.zip"

    image_zip = tmp_path / "image-a32-test.zip"
    with zipfile.ZipFile(image_zip, "w") as image:
        image.writestr("boot.img", b"boot")

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("image-a32-test.zip", image_zip.read_bytes())
        archive.writestr("flash-all.bat", b"@echo off")
        archive.writestr("flash-all.sh", b"#!/bin/sh")

    result = FirmwarePackageInspector().inspect(package)

    assert result["build_identity"] == {
        "device_codename": "UNKNOWN",
        "build_id": "UNKNOWN",
        "android_release": "UNKNOWN",
        "security_patch": "UNKNOWN",
    }
    assert result["build_identity_source"] == "UNKNOWN"

def test_factory_package_inspection_incomplete_build_metadata_is_unknown(tmp_path):
    package = tmp_path / "a32-factory.zip"

    image_zip = tmp_path / "image-a32-test.zip"
    with zipfile.ZipFile(image_zip, "w") as image:
        image.writestr(
            "android-info.txt",
            "\n".join(
                [
                    "board=a32",
                    "build_id=AQ3A.240829.003",
                ]
            ).encode(),
        )
        image.writestr("boot.img", b"boot")

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("image-a32-test.zip", image_zip.read_bytes())
        archive.writestr("flash-all.bat", b"@echo off")
        archive.writestr("flash-all.sh", b"#!/bin/sh")

    result = FirmwarePackageInspector().inspect(package)

    assert result["build_identity"] == {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "UNKNOWN",
        "security_patch": "UNKNOWN",
    }
    assert result["build_identity_source"] == "android-info.txt"

def test_factory_package_inspection_malformed_build_metadata_is_unknown(tmp_path):
    package = tmp_path / "a32-factory.zip"

    image_zip = tmp_path / "image-a32-test.zip"
    with zipfile.ZipFile(image_zip, "w") as image:
        image.writestr(
            "android-info.txt",
            "\n".join(
                [
                    "board=",
                    "build_id=",
                    "android_version=not-a-version",
                    "security_patch=not-a-date",
                ]
            ).encode(),
        )
        image.writestr("boot.img", b"boot")

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("image-a32-test.zip", image_zip.read_bytes())
        archive.writestr("flash-all.bat", b"@echo off")
        archive.writestr("flash-all.sh", b"#!/bin/sh")

    result = FirmwarePackageInspector().inspect(package)

    assert result["build_identity"] == {
        "device_codename": "UNKNOWN",
        "build_id": "UNKNOWN",
        "android_release": "UNKNOWN",
        "security_patch": "UNKNOWN",
    }
    assert result["build_identity_source"] == "UNKNOWN"

def test_firmware_package_compatibility_matches_real_device_identity():
    package_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    device_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }

    result = FirmwareCompatibilityChecker().compare(
        package_identity,
        device_identity,
    )

    assert result["verification"] == "PASS"
    assert result["reason"] == "PACKAGE_DEVICE_IDENTITY_MATCH"

def test_firmware_package_compatibility_rejects_conflicting_build_identity():
    package_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    device_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.250101.001",
        "android_release": "15",
        "security_patch": "2025-01-01",
    }

    result = FirmwareCompatibilityChecker().compare(
        package_identity,
        device_identity,
    )

    assert result["verification"] == "FAIL"
    assert result["reason"] == "PACKAGE_DEVICE_IDENTITY_CONFLICT"

def test_firmware_package_compatibility_rejects_conflicting_device_codename():
    package_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    device_identity = {
        "device_codename": "other-device",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }

    result = FirmwareCompatibilityChecker().compare(
        package_identity,
        device_identity,
    )

    assert result["verification"] == "FAIL"
    assert result["reason"] == "PACKAGE_DEVICE_IDENTITY_CONFLICT"

def test_firmware_package_compatibility_requires_complete_identity_evidence():
    package_identity = {
        "device_codename": "a32",
        "build_id": "UNKNOWN",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    device_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }

    result = FirmwareCompatibilityChecker().compare(
        package_identity,
        device_identity,
    )

    assert result["verification"] == "UNKNOWN"
    assert result["reason"] == "INSUFFICIENT_IDENTITY_EVIDENCE"

def test_firmware_package_compatibility_rejects_conflicting_android_release():
    package_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    device_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "14",
        "security_patch": "2024-09-01",
    }

    result = FirmwareCompatibilityChecker().compare(
        package_identity,
        device_identity,
    )

    assert result["verification"] == "FAIL"
    assert result["reason"] == "PACKAGE_DEVICE_IDENTITY_CONFLICT"

def test_firmware_package_compatibility_rejects_conflicting_security_patch():
    package_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
    device_identity = {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2025-01-01",
    }

    result = FirmwareCompatibilityChecker().compare(
        package_identity,
        device_identity,
    )

    assert result["verification"] == "FAIL"
    assert result["reason"] == "PACKAGE_DEVICE_IDENTITY_CONFLICT"


def test_google_firmware_source_resolver_returns_official_candidate():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceResolver

    resolver = GoogleFirmwareSourceResolver()

    result = resolver.find_candidates(
        {
            "device_codename": "shiba",
            "build_id": "AQ3A.240829.003",
            "android_release": "15",
            "security_patch": "2024-09-01",
        }
    )

    assert result["source"] == "GOOGLE"
    assert result["repository"] in {"FACTORY_IMAGES", "FULL_OTA"}
    assert result["availability"] == "OFFICIAL_SOURCE"

def test_firmware_candidate_contract_contains_exact_metadata():
    from app.core.firmware_source_resolver import FirmwareCandidate

    candidate = FirmwareCandidate(
        source="GOOGLE",
        repository="FACTORY_IMAGES",
        device_codename="shiba",
        build_id="AQ3A.240829.003",
        android_release="15",
        security_patch="2024-09-01",
        release_date="2024-09-05",
        package_url="https://example.invalid/factory.zip",
        package_sha256="abc123",
        source_verified=True,
        candidate_verified=False,
        verification="UNKNOWN",
    )

    assert candidate.source == "GOOGLE"
    assert candidate.repository == "FACTORY_IMAGES"
    assert candidate.device_codename == "shiba"
    assert candidate.build_id == "AQ3A.240829.003"
    assert candidate.android_release == "15"
    assert candidate.security_patch == "2024-09-01"
    assert candidate.release_date == "2024-09-05"
    assert candidate.package_url.endswith("factory.zip")
    assert candidate.package_sha256 == "abc123"
    assert candidate.source_verified is True
    assert candidate.candidate_verified is False
    assert candidate.verification == "UNKNOWN"


def test_firmware_candidate_missing_metadata_is_unknown():
    from app.core.firmware_source_resolver import FirmwareCandidate

    candidate = FirmwareCandidate(
        source="GOOGLE",
        repository="FACTORY_IMAGES",
        device_codename="shiba",
        build_id="UNKNOWN",
        android_release="UNKNOWN",
        security_patch="UNKNOWN",
        release_date="UNKNOWN",
        package_url="UNKNOWN",
        package_sha256="UNKNOWN",
        source_verified=True,
        candidate_verified=False,
        verification="UNKNOWN",
    )

    assert candidate.verification == "UNKNOWN"
    assert candidate.candidate_verified is False


def test_firmware_candidate_missing_sha256_is_not_verified():
    from app.core.firmware_source_resolver import FirmwareCandidate

    candidate = FirmwareCandidate(
        source="GOOGLE",
        repository="FACTORY_IMAGES",
        device_codename="shiba",
        build_id="AQ3A.240829.003",
        android_release="15",
        security_patch="2024-09-01",
        release_date="2024-09-05",
        package_url="https://example.invalid/factory.zip",
        package_sha256="UNKNOWN",
        source_verified=True,
        candidate_verified=False,
        verification="UNKNOWN",
    )

    assert candidate.package_sha256 == "UNKNOWN"
    assert candidate.candidate_verified is False
    assert candidate.verification == "UNKNOWN"


def test_firmware_candidate_unknown_device_is_not_verified():
    from app.core.firmware_source_resolver import FirmwareCandidate

    candidate = FirmwareCandidate(
        source="GOOGLE",
        repository="UNKNOWN",
        device_codename="UNKNOWN",
        build_id="UNKNOWN",
        android_release="UNKNOWN",
        security_patch="UNKNOWN",
        release_date="UNKNOWN",
        package_url="UNKNOWN",
        package_sha256="UNKNOWN",
        source_verified=False,
        candidate_verified=False,
        verification="UNKNOWN",
    )

    assert candidate.device_codename == "UNKNOWN"
    assert candidate.repository == "UNKNOWN"
    assert candidate.source_verified is False
    assert candidate.candidate_verified is False
    assert candidate.verification == "UNKNOWN"

def test_google_candidate_normalizer_preserves_exact_metadata():
    from app.core.firmware_source_resolver import GoogleFirmwareCandidateNormalizer

    normalizer = GoogleFirmwareCandidateNormalizer()

    result = normalizer.normalize(
        {
            "source": "GOOGLE",
            "repository": "FACTORY_IMAGES",
            "device_codename": "shiba",
            "build_id": "AQ3A.240829.003",
            "android_release": "15",
            "security_patch": "2024-09-01",
            "release_date": "2024-09-03",
            "package_url": "https://dl.google.com/example-factory.zip",
            "package_sha256": "abc123",
            "vbmeta_digest": "def456",
        }
    )

    assert result["source"] == "GOOGLE"
    assert result["repository"] == "FACTORY_IMAGES"
    assert result["device_codename"] == "shiba"
    assert result["build_id"] == "AQ3A.240829.003"
    assert result["android_release"] == "15"
    assert result["security_patch"] == "2024-09-01"
    assert result["release_date"] == "2024-09-03"
    assert result["package_url"] == "https://dl.google.com/example-factory.zip"
    assert result["package_sha256"] == "abc123"
    assert result["vbmeta_digest"] == "def456"


def test_google_candidate_normalizer_missing_package_sha256_is_unknown():
    from app.core.firmware_source_resolver import GoogleFirmwareCandidateNormalizer

    normalizer = GoogleFirmwareCandidateNormalizer()

    result = normalizer.normalize(
        {
            "source": "GOOGLE",
            "repository": "FACTORY_IMAGES",
            "device_codename": "shiba",
            "build_id": "AQ3A.240829.003",
            "android_release": "15",
            "security_patch": "2024-09-01",
            "release_date": "2024-09-03",
            "package_url": "https://dl.google.com/example-factory.zip",
            "package_sha256": "",
            "vbmeta_digest": "def456",
        }
    )

    assert result["package_sha256"] == "UNKNOWN"
    assert result["verification"] == "UNKNOWN"


def test_google_candidate_normalizer_missing_required_metadata_is_unknown():
    from app.core.firmware_source_resolver import GoogleFirmwareCandidateNormalizer

    normalizer = GoogleFirmwareCandidateNormalizer()

    result = normalizer.normalize(
        {
            "source": "GOOGLE",
            "repository": "FACTORY_IMAGES",
            "device_codename": "shiba",
            "build_id": "",
            "android_release": "15",
            "security_patch": "2024-09-01",
            "release_date": "2024-09-03",
            "package_url": "https://dl.google.com/example-factory.zip",
        }
    )

    assert result["verification"] == "UNKNOWN"
    assert result["candidate_verified"] is False


def test_google_candidate_normalizer_distinguishes_full_ota():
    from app.core.firmware_source_resolver import GoogleFirmwareCandidateNormalizer

    normalizer = GoogleFirmwareCandidateNormalizer()

    result = normalizer.normalize(
        {
            "source": "GOOGLE",
            "repository": "FULL_OTA",
            "device_codename": "shiba",
            "build_id": "AQ3A.240829.003",
            "android_release": "15",
            "security_patch": "2024-09-01",
            "release_date": "2024-09-03",
            "package_url": "https://dl.google.com/example-ota.zip",
        }
    )

    assert result["repository"] == "FULL_OTA"
    assert result["source"] == "GOOGLE"
    assert result["verification"] == "UNKNOWN"


def test_google_candidate_normalizer_does_not_mark_unverified_candidate_pass():
    from app.core.firmware_source_resolver import GoogleFirmwareCandidateNormalizer

    normalizer = GoogleFirmwareCandidateNormalizer()

    result = normalizer.normalize(
        {
            "source": "GOOGLE",
            "repository": "FACTORY_IMAGES",
            "device_codename": "shiba",
            "build_id": "AQ3A.240829.003",
            "android_release": "15",
            "security_patch": "2024-09-01",
            "release_date": "2024-09-03",
            "package_url": "https://dl.google.com/example-factory.zip",
        }
    )

    assert result["source_verified"] is False
    assert result["candidate_verified"] is False
    assert result["verification"] != "PASS"

def test_google_source_reader_requires_official_source_reference():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.read_source(
        "https://developers.google.com/android/images"
    )

    assert result["source"] == "GOOGLE"
    assert result["repository"] == "FACTORY_IMAGES"
    assert result["official_source"] is True
    assert result["evidence_reference"]


def test_google_source_reader_rejects_non_official_source():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.read_source(
        "https://example.com/firmware"
    )

    assert result["official_source"] is False
    assert result["verification"] == "UNKNOWN"


def test_google_source_reader_does_not_invent_missing_candidate_metadata():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.read_candidate(
        {
            "device_codename": "shiba",
            "build_id": "",
            "android_release": "",
            "security_patch": "",
            "release_date": "",
            "package_url": "",
        }
    )

    assert result["candidate_verified"] is False
    assert result["verification"] == "UNKNOWN"


def test_google_source_reader_preserves_factory_and_full_ota_source_families():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    factory = reader.read_source(
        "https://developers.google.com/android/images"
    )
    ota = reader.read_source(
        "https://developers.google.com/android/ota"
    )

    assert factory["repository"] == "FACTORY_IMAGES"
    assert ota["repository"] == "FULL_OTA"
    assert factory["source"] == "GOOGLE"
    assert ota["source"] == "GOOGLE"


def test_google_source_reader_never_marks_unverified_candidate_pass():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.read_candidate(
        {
            "device_codename": "shiba",
            "build_id": "AQ3A.240829.003",
            "android_release": "15",
            "security_patch": "2024-09-01",
            "release_date": "2024-09-03",
            "package_url": "https://dl.google.com/example.zip",
        }
    )

    assert result["candidate_verified"] is False
    assert result["verification"] != "PASS"

def test_google_source_reader_fetches_official_page_evidence():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.fetch_source(
        "https://developers.google.com/android/images"
    )

    assert result["source"] == "GOOGLE"
    assert result["repository"] == "FACTORY_IMAGES"
    assert result["official_source"] is True
    assert result["verification"] == "UNKNOWN"
    assert result["evidence_reference"]
    assert result["raw_source_evidence"]


def test_google_source_reader_does_not_accept_non_official_page():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.fetch_source(
        "https://example.com/firmware"
    )

    assert result["official_source"] is False
    assert result["verification"] == "UNKNOWN"
    assert result["raw_source_evidence"] == ""


def test_google_source_reader_extracts_candidate_metadata_from_real_source():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    source = {
        "source": "GOOGLE",
        "repository": "FACTORY_IMAGES",
        "official_source": True,
        "evidence_reference": "https://developers.google.com/android/images",
        "raw_source_evidence": (
            "device=shiba "
            "build=AQ3A.TEST "
            "android=15 "
            "security_patch=2024-09-01 "
            "release_date=2024-09-03 "
            "package_url=https://dl.google.com/test.zip"
        ),
    }

    result = reader.extract_candidates(source)

    assert result
    assert result[0]["device_codename"] == "shiba"
    assert result[0]["build_id"] == "AQ3A.TEST"
    assert result[0]["android_release"] == "15"
    assert result[0]["security_patch"] == "2024-09-01"
    assert result[0]["release_date"] == "2024-09-03"
    assert result[0]["package_url"] == "https://dl.google.com/test.zip"


def test_google_source_reader_missing_source_evidence_stays_unknown():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    result = reader.extract_candidates(
        {
            "source": "GOOGLE",
            "repository": "FACTORY_IMAGES",
            "official_source": True,
            "evidence_reference": "https://developers.google.com/android/images",
            "raw_source_evidence": "",
        }
    )

    assert result == []


def test_google_source_reader_never_invents_package_sha256():
    from app.core.firmware_source_resolver import GoogleFirmwareSourceReader

    reader = GoogleFirmwareSourceReader()

    source = {
        "source": "GOOGLE",
        "repository": "FACTORY_IMAGES",
        "official_source": True,
        "evidence_reference": "https://developers.google.com/android/images",
        "raw_source_evidence": (
            "device=shiba "
            "build=AQ3A.TEST "
            "android=15 "
            "security_patch=2024-09-01 "
            "release_date=2024-09-03 "
            "package_url=https://dl.google.com/test.zip"
        ),
    }

    result = reader.extract_candidates(source)

    assert result
    assert result[0]["package_sha256"] == "UNKNOWN"
    assert result[0]["candidate_verified"] is False
    assert result[0]["verification"] == "UNKNOWN"

def test_firmware_source_adapter_contract_exists():
    from app.core.firmware_source_resolver import FirmwareSourceAdapter

    adapter = FirmwareSourceAdapter()

    assert hasattr(adapter, "identify_source")
    assert hasattr(adapter, "fetch_candidates")
    assert hasattr(adapter, "normalize_candidate")


def test_firmware_source_adapter_unknown_source_stays_unknown():
    from app.core.firmware_source_resolver import FirmwareSourceAdapter

    adapter = FirmwareSourceAdapter()

    result = adapter.identify_source("https://example.com/firmware")

    assert result["source"] == "UNKNOWN"
    assert result["official_source"] is False
    assert result["verification"] == "UNKNOWN"


def test_firmware_source_adapter_missing_candidate_metadata_stays_unknown():
    from app.core.firmware_source_resolver import FirmwareSourceAdapter

    adapter = FirmwareSourceAdapter()

    result = adapter.normalize_candidate({})

    assert result["candidate_verified"] is False
    assert result["verification"] == "UNKNOWN"


def test_firmware_source_adapter_never_invents_package_sha256():
    from app.core.firmware_source_resolver import FirmwareSourceAdapter

    adapter = FirmwareSourceAdapter()

    result = adapter.normalize_candidate(
        {
            "source": "TEST",
            "repository": "OFFICIAL",
            "device_codename": "test",
            "build_id": "TEST.BUILD",
            "android_release": "15",
            "security_patch": "2026-01-01",
            "release_date": "2026-01-02",
            "package_url": "https://example.com/test.zip",
        }
    )

    assert result["package_sha256"] == "UNKNOWN"
    assert result["candidate_verified"] is False
    assert result["verification"] == "UNKNOWN"
