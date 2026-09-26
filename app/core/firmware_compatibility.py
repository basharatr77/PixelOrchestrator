class FirmwareCompatibilityChecker:
    def compare(self, package_identity, device_identity):
        fields = (
            "device_codename",
            "build_id",
            "android_release",
            "security_patch",
        )

        for field in fields:
            package_value = package_identity.get(field)
            device_value = device_identity.get(field)

            if package_value in (None, "", "UNKNOWN") or device_value in (
                None,
                "",
                "UNKNOWN",
            ):
                return {
                    "verification": "UNKNOWN",
                    "reason": "INSUFFICIENT_IDENTITY_EVIDENCE",
                }

            if package_value != device_value:
                return {
                    "verification": "FAIL",
                    "reason": "PACKAGE_DEVICE_IDENTITY_CONFLICT",
                }

        return {
            "verification": "PASS",
            "reason": "PACKAGE_DEVICE_IDENTITY_MATCH",
        }
