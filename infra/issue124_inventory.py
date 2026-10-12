"""Read-only Docker inventory for issue #124's Owner deletion gate.

Prints no environment variables, site configuration, credentials, or volume data.
"""

import json
import pathlib
import subprocess
from collections import defaultdict


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def inventory():
    ids = output("docker", "ps", "-aq", "--no-trunc").splitlines()
    containers = json.loads(output("docker", "inspect", *ids)) if ids else []
    cc = []
    other = []
    volume_users = defaultdict(list)
    image_users = defaultdict(list)
    for item in containers:
        name = item["Name"].lstrip("/")
        labels = item["Config"].get("Labels") or {}
        project = labels.get("com.docker.compose.project", "")
        row = {
            "id": item["Id"],
            "name": name,
            "project": project,
            "state": item["State"]["Status"],
        }
        (cc if "centrochange" in name.lower() or "centrochange" in project.lower() else other).append(row)
        image_users[item["Image"]].append(name)
        for mount in item["Mounts"]:
            if mount["Type"] == "volume":
                volume_users[mount["Name"]].append(name)
    volumes = []
    preserved_volumes = []
    for name in output("docker", "volume", "ls", "-q").splitlines():
        users = sorted(set(volume_users[name]))
        owned = "centrochange" in name.lower() or (
            users and all("centrochange" in user.lower() for user in users)
        )
        row = {"name": name, "users": users}
        (volumes if owned and not name.startswith("buildx_") and all("centrochange" in user.lower() for user in users) else preserved_volumes).append(row)
    networks = []
    preserved_networks = []
    for name in output("docker", "network", "ls", "--format", "{{.Name}}").splitlines():
        data = json.loads(output("docker", "network", "inspect", name))[0]
        members = sorted(data.get("Containers") or {})
        row = {"id": data["Id"], "name": name, "members": members}
        (networks if "centrochange" in name.lower() else preserved_networks).append(row)
    images = []
    for line in output("docker", "image", "ls", "-a", "--no-trunc", "--format", "{{json .}}").splitlines():
        row = json.loads(line)
        if "centrochange" in row.get("Repository", "").lower():
            images.append({"id": row["ID"], "repository": row["Repository"], "tag": row["Tag"]})
    state_root = pathlib.Path("/home/empv26/.local/state")
    state_paths = []
    source_paths = []
    for path in sorted(state_root.glob("centrochange*")):
        if not path.exists():
            continue
        if (path / ".git").exists() or (path / "repo" / ".git").exists() or (path / "product" / ".git").exists():
            source_paths.append(str(path))
        else:
            state_paths.append(str(path))
    return {
        "delete_after_owner_gate": {
            "containers": sorted(cc, key=lambda x: x["name"]),
            "volumes": sorted(volumes, key=lambda x: x["name"]),
            "networks": sorted(networks, key=lambda x: x["name"]),
            "state_paths": state_paths,
        },
        "preserve": {
            "containers": sorted(other, key=lambda x: x["name"]),
            "volumes": sorted(preserved_volumes, key=lambda x: x["name"]),
            "networks": sorted(preserved_networks, key=lambda x: x["name"]),
            "images_until_new_stack_validated": sorted(images, key=lambda x: (x["repository"], x["tag"])),
            "local_source_repositories": source_paths,
        },
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), indent=2, sort_keys=True))
