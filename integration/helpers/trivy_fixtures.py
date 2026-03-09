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

# Partial scan — only openssl (libexpat1 absent vs SCAN_V1).
# Used to verify that findings missing from a follow-up scan are marked FIXED.
SCAN_V1_PARTIAL: dict = {
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

# Second image with a single MEDIUM unfixable finding.
# Used in multi-image tests (sort, filter) alongside SCAN_V1.
SCAN_REDIS: dict = {
    "ArtifactName": "redis:7.0",
    "ArtifactType": "container_image",
    "Results": [
        {
            "Target": "redis:7.0 (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-9010",
                    "PkgName": "curl",
                    "InstalledVersion": "7.88.1-10",
                    "Severity": "MEDIUM",
                    "Title": "curl: protocol confusion in URL parsing",
                },
            ],
        }
    ],
}

# Misconfig scan — plex container with two misconfigurations.
# PRIV_001 (HIGH): privileged mode
# NET_001 (MEDIUM): host network mode
MISCONFIG_V1: dict = {
    "image_name": "linuxserver/plex:latest",
    "container_name": "plex",
    "findings": [
        {
            "check_id": "PRIV_001",
            "severity": "HIGH",
            "title": "Container running in privileged mode",
            "fix_guideline": "Remove 'privileged: true' from the container definition.",
        },
        {
            "check_id": "NET_001",
            "severity": "MEDIUM",
            "title": "Container using host network mode",
            "fix_guideline": "Remove 'network_mode: host' from the container definition.",
        },
    ],
}

# Clean misconfig scan for the same plex container — no findings.
# Sending this after MISCONFIG_V1 causes the hub to mark PRIV_001 and NET_001 as fixed.
MISCONFIG_CLEAN: dict = {
    "image_name": "linuxserver/plex:latest",
    "container_name": "plex",
    "findings": [],
}
