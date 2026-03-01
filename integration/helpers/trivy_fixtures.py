"""
Pre-built Trivy scan JSON payloads for integration tests.

The aggregator reads:
- scan_data["ArtifactName"]         → image name (used as Container.image_name)
- scan_data["Results"][*]["Vulnerabilities"][*]["VulnerabilityID"]
- scan_data["Results"][*]["Vulnerabilities"][*]["PkgName"]
- scan_data["Results"][*]["Vulnerabilities"][*]["InstalledVersion"]
- scan_data["Results"][*]["Vulnerabilities"][*]["FixedVersion"]
- scan_data["Results"][*]["Vulnerabilities"][*]["Severity"]
"""

# Primary scan payload — 2 findings (1 CRITICAL, 1 HIGH).
# Used by most tests that need to seed findings.
SCAN_V1: dict = {
    "ArtifactName": "nginx:1.27",
    "ArtifactType": "container_image",
    "Results": [
        {
            "Target": "nginx:1.27 (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-9000",
                    "PkgName": "openssl",
                    "InstalledVersion": "3.0.11-1~deb12u2",
                    "FixedVersion": "3.0.11-1~deb12u3",
                    "Severity": "CRITICAL",
                    "Title": "OpenSSL: buffer overflow in X.509 parsing",
                },
                {
                    "VulnerabilityID": "CVE-2024-9001",
                    "PkgName": "libexpat1",
                    "InstalledVersion": "2.5.0-1",
                    "FixedVersion": "2.5.0-2",
                    "Severity": "HIGH",
                    "Title": "Expat: use-after-free in XML parsing",
                },
            ],
        }
    ],
}

# Second scan payload — only a MEDIUM finding.
# Used to verify that re-scanning with different results works correctly.
SCAN_V2: dict = {
    "ArtifactName": "nginx:1.27",
    "ArtifactType": "container_image",
    "Results": [
        {
            "Target": "nginx:1.27 (debian 12.9)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-9002",
                    "PkgName": "zlib1g",
                    "InstalledVersion": "1:1.2.13.dfsg-1",
                    "FixedVersion": "1:1.2.13.dfsg-2",
                    "Severity": "MEDIUM",
                    "Title": "zlib: heap buffer overflow",
                },
            ],
        }
    ],
}

# Empty scan — no vulnerabilities found.
SCAN_CLEAN: dict = {
    "ArtifactName": "alpine:3.21",
    "ArtifactType": "container_image",
    "Results": [],
}
