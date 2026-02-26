#!/usr/bin/env python3
"""Collect project IAM policy evidence grouped by principal."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List

from google.api_core import exceptions as gcp_exceptions
from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2


LOGGER = logging.getLogger(__name__)
INVALID_FILENAME_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")
SUPPORTED_PRINCIPAL_TYPES = ("user", "group", "serviceAccount")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect project-level IAM bindings and write evidence by principal."
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="Target GCP project ID.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for evidence files.",
    )
    return parser.parse_args()


def sanitize_principal(principal: str) -> str:
    """Sanitize principal value so it can be safely used as a filename."""
    cleaned = INVALID_FILENAME_CHARS.sub("_", principal.strip())
    return cleaned.strip("._") or "unknown_principal"


def split_principal(principal: str) -> tuple[str | None, str]:
    """Split a principal into type and identity (for example user:alice@example.com)."""
    if ":" not in principal:
        return None, principal

    principal_type, identity = principal.split(":", 1)
    if principal_type not in SUPPORTED_PRINCIPAL_TYPES:
        return None, identity

    return principal_type, identity


def fetch_project_policy(project_id: str) -> policy_pb2.Policy:
    client = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{project_id}"

    request = iam_policy_pb2.GetIamPolicyRequest(resource=resource)
    return client.get_iam_policy(request=request)


def group_bindings_by_principal(
    bindings: List[resourcemanager_v3.Binding],
) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}

    for binding in bindings:
        role = binding.role

        for principal in binding.members:
            roles = grouped.setdefault(principal, [])
            if role not in roles:
                roles.append(role)

    return grouped


def write_evidence_files(output_dir: Path, project_id: str, grouped: Dict[str, List[str]]) -> None:
    base_dir = output_dir / "by_principal"
    base_dir.mkdir(parents=True, exist_ok=True)
    for principal_type in SUPPORTED_PRINCIPAL_TYPES:
        (base_dir / principal_type).mkdir(parents=True, exist_ok=True)

    for principal, roles in grouped.items():
        principal_type, principal_identity = split_principal(principal)
        if principal_type is None:
            LOGGER.warning("Skipping unsupported principal format: %s", principal)
            continue

        payload = {
            "principal": {
                "name": principal,
                "project": project_id,
                "roles": roles,
            }
        }
        filename = sanitize_principal(principal_identity) + ".json"
        destination = base_dir / principal_type / filename
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    args = parse_args()
    output_dir = Path(args.output_dir)

    try:
        policy = fetch_project_policy(args.project_id)
        grouped = group_bindings_by_principal(policy.bindings)
        write_evidence_files(output_dir, args.project_id, grouped)
        LOGGER.info(
            "Collected %d principals from project %s into %s",
            len(grouped),
            args.project_id,
            output_dir,
        )
        return 0
    except gcp_exceptions.GoogleAPICallError as err:
        LOGGER.error("GCP API error while collecting IAM policy: %s", err)
    except gcp_exceptions.RetryError as err:
        LOGGER.error("Retry error while collecting IAM policy: %s", err)
    except PermissionError as err:
        LOGGER.error("Filesystem permission error writing evidence: %s", err)
    except OSError as err:
        LOGGER.error("I/O error writing evidence: %s", err)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
