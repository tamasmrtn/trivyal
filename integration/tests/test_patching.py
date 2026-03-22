"""Integration tests for the Copa patching flow.

Uses SimulatedAgent to test the full patch lifecycle without a real patcher sidecar.
"""

import asyncio
import json


class TestPatchFlow:
    async def test_create_patch_returns_201_for_connected_agent(self, hub, registered_agent, connected_agent):
        """Create a patch request for a connected agent with patching available."""
        agent_id = registered_agent["id"]

        # Send host_metadata with patching_available
        await connected_agent.send(json.dumps({
            "type": "host_metadata",
            "metadata": {"patching_available": True, "hostname": "test"},
        }))
        await asyncio.sleep(0.5)  # Let hub process the message

        # Create a container via scan result
        scan_data = {
            "ArtifactName": "nginx:1.25",
            "Results": [{
                "Vulnerabilities": [{
                    "VulnerabilityID": "CVE-2024-0001",
                    "PkgName": "openssl",
                    "InstalledVersion": "3.1.4",
                    "FixedVersion": "3.1.7",
                    "Severity": "HIGH",
                }]
            }],
        }
        await connected_agent.send(json.dumps({
            "type": "scan_result",
            "data": scan_data,
            "container_name": "my-nginx",
        }))
        await asyncio.sleep(0.5)

        # Get the container ID from the images list
        images_resp = await hub.get("/api/v1/images")
        images_resp.raise_for_status()
        images = images_resp.json()["data"]
        assert len(images) > 0

        # Find container via agent scans
        scans_resp = await hub.get(f"/api/v1/agents/{agent_id}/scans")
        scans_resp.raise_for_status()
        scans = scans_resp.json()["data"]
        assert len(scans) > 0
        container_id = scans[0]["container_id"]

        # Create the patch
        patch_resp = await hub.post("/api/v1/patches", json={
            "agent_id": agent_id,
            "container_id": container_id,
            "image_name": "nginx:1.25",
        })
        assert patch_resp.status_code == 201
        patch_data = patch_resp.json()
        assert patch_data["status"] in ("pending", "running")

        # Agent should receive a patch_trigger message
        msg = await asyncio.wait_for(connected_agent.recv(), timeout=5.0)
        trigger = json.loads(msg)
        assert trigger["type"] == "patch_trigger"
        assert trigger["request_id"] == patch_data["id"]

        # Simulate patch completion
        await connected_agent.send(json.dumps({
            "type": "patch_log",
            "request_id": patch_data["id"],
            "line": "Patching openssl...",
        }))
        await connected_agent.send(json.dumps({
            "type": "patch_result",
            "request_id": patch_data["id"],
            "status": "completed",
            "patched_tag": "nginx:1.25-trivyal-patched",
        }))
        await asyncio.sleep(0.5)

        # Verify patch is completed
        get_resp = await hub.get(f"/api/v1/patches/{patch_data['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "completed"
        assert get_resp.json()["patched_tag"] == "nginx:1.25-trivyal-patched"


class TestPatchDisconnectedAgent:
    async def test_returns_409_when_agent_not_connected(self, hub, registered_agent):
        resp = await hub.post("/api/v1/patches", json={
            "agent_id": registered_agent["id"],
            "container_id": "fake-cid",
            "image_name": "nginx",
        })
        assert resp.status_code == 409


class TestPatchSummary:
    async def test_returns_summary(self, hub):
        resp = await hub.get("/api/v1/dashboard/patch-summary")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_patched" in body
        assert "findings_resolved" in body
        assert "patching_available" in body
