from dataclasses import dataclass
from typing import Optional, List
import json
import os
import subprocess
import urllib.request
from urllib.parse import urlparse

from utils.ods_ssh import executeRemoteShCommandAndGetOutput


@dataclass
class Artifact:
    id: str
    url: str
    action: str = "download"


@dataclass
class Package:
    packageId: str
    version: str
    artifacts: List[Artifact]

    def get_artifact(self, artifact_id: str) -> "Artifact":
        artifact = next((a for a in self.artifacts if a.id == artifact_id), None)
        if not artifact:
            raise RuntimeError(f"Artifact '{artifact_id}' not found in package '{self.packageId}'")
        return artifact


def parse_package_file(file_path: str) -> Package:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    artifacts = [
        Artifact(
            id=a["id"],
            url=a["url"],
            action=a.get("action", "download"),
        )
        for a in data.get("artifacts", [])
    ]

    return Package(
        packageId=data["packageId"],
        version=data["version"],
        artifacts=artifacts,
    )


def get_artifact_url(package: Package, artifact_id: str) -> Optional[str]:
    for artifact in package.artifacts:
        if artifact.id == artifact_id:
            return artifact.url
    return None


def _is_s3_url(url: str) -> bool:
    return urlparse(url).scheme == "s3"


def _check_aws_credentials() -> None:
    """Verify AWS credentials are reachable before attempting S3 access.

    boto3 checks in this order:
      1. Environment variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
      2. ~/.aws/credentials
      3. ~/.aws/config (for SSO / assumed roles)
    """
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return  # env-var credentials present

    creds_path = os.path.expanduser("~/.aws/credentials")
    config_path = os.path.expanduser("~/.aws/config")

    if not os.path.exists(creds_path) and not os.path.exists(config_path):
        raise RuntimeError(
            f"AWS credentials not found. Expected at '{creds_path}'.\n"
            "To fix: run 'aws configure' on this machine, or set "
            "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
        )

    profile = os.environ.get("AWS_PROFILE")
    if not profile:
        raise RuntimeError(
            "AWS_PROFILE is not set. The credentials file uses a named profile.\n"
            "To fix: export AWS_PROFILE=<profile_name> (check profile name with: cat ~/.aws/credentials)"
        )


def _download_from_s3(url: str, dest_dir: str) -> str:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    _check_aws_credentials()

    parsed = urlparse(url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    filename = os.path.basename(key)

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)

    try:
        profile = os.environ.get("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3 = session.client("s3")
        s3.download_file(bucket, key, dest_path)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 download failed for '{url}': {e}") from e

    return dest_path


def _download_from_http(url: str, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)

    filename = os.path.basename(urlparse(url).path)
    dest_path = os.path.join(dest_dir, filename)

    urllib.request.urlretrieve(url, dest_path)

    return dest_path


def download_artifact(url: str, dest_dir: str) -> str:
    if not url:
        raise ValueError("URL is empty or None")

    if _is_s3_url(url):
        return _download_from_s3(url, dest_dir)
    return _download_from_http(url, dest_dir)


def run_artifact(url: str, dest_dir: str, host: str, user: str, params: str = "") -> str:
    dest_path = download_artifact(url, dest_dir)
    output = executeRemoteShCommandAndGetOutput(host, user, params, dest_path)
    return output.decode("utf-8") if isinstance(output, bytes) else output


def process_artifact(
    artifact: Artifact,
    dest_dir: str,
    host: Optional[str] = None,
    user: Optional[str] = None,
    params: str = "",
) -> Optional[str]:
    if artifact.action == "download":
        return download_artifact(artifact.url, dest_dir)
    elif artifact.action == "run":
        if not host or not user:
            raise ValueError(
                f"'host' and 'user' are required for action 'run' (artifact: '{artifact.id}')"
            )
        return run_artifact(artifact.url, dest_dir, host, user, params)
    elif artifact.action == "download_and_run":
        dest_path = download_artifact(artifact.url, dest_dir)
        os.chmod(dest_path, 0o755)
        subprocess.run(["bash", dest_path], check=True)
        return dest_path
    else:
        raise ValueError(f"Unknown action '{artifact.action}' for artifact '{artifact.id}'")


def process_artifact_by_id(
    pkg: Package,
    artifact_id: str,
    dest_dir: str,
    host: Optional[str] = None,
    user: Optional[str] = None,
    params: str = "",
) -> Optional[str]:
    return process_artifact(pkg.get_artifact(artifact_id), dest_dir, host=host, user=user, params=params)
