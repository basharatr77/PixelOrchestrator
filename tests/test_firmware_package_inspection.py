from hashlib import sha256
from pathlib import Path
import zipfile

from app.core.firmware_package_inspector import FirmwarePackageInspector


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
