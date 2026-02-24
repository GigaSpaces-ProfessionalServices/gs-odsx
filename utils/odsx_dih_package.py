from dataclasses import dataclass
from typing import Optional, List
import json
import os
import urllib.request
from urllib.parse import urlparse

@dataclass
class Artifact:
    id: str
    url: str

@dataclass
class Package:
    packageId: str
    version: str
    artifacts: List[Artifact]

def parse_package_file(file_path: str) -> Package:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    artifacts = [Artifact(**a) for a in data.get("artifacts", [])]

    return Package(
        packageId=data["packageId"],
        version=data["version"],
        artifacts=artifacts
    )

def get_artifact_url(package: Package, artifact_id: str) -> Optional[str]:
    for artifact in package.artifacts:
        if artifact.id == artifact_id:
            return artifact.url
    return None

def download_artifact(url: str, dest_dir: str) -> str:
    if not url:
        raise ValueError("URL is empty or None")

    os.makedirs(dest_dir, exist_ok=True)

    filename = os.path.basename(urlparse(url).path)
    dest_path = os.path.join(dest_dir, filename)

    urllib.request.urlretrieve(url, dest_path)

    return dest_path
