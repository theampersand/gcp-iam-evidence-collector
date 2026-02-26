import json
import logging
from pathlib import Path

import pytest

from src.main import group_bindings_by_principal, write_evidence_files

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeBinding:
    def __init__(self, role: str, members: list[str]) -> None:
        self.role = role
        self.members = members


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_fixture(name: str) -> dict:
    return read_json(FIXTURES_DIR / name)


def test_group_bindings_by_principal_deduplicates_roles_and_preserves_order() -> None:
    bindings_fixture = read_fixture("bindings_dedup.json")
    bindings = [FakeBinding(item["role"], item["members"]) for item in bindings_fixture]

    grouped = group_bindings_by_principal(bindings)

    assert grouped["user:alice@example.com"] == ["roles/viewer", "roles/editor"]


def test_write_evidence_files_writes_expected_schema(tmp_path: Path) -> None:
    grouped = read_fixture("grouped_service_account.json")
    expected = read_fixture("expected_service_account_output.json")

    write_evidence_files(tmp_path, "ecommerce-microservices-488523", grouped)

    output_file = (
        tmp_path
        / "by_principal"
        / "serviceAccount"
        / "my-service-account-1_ecommerce-microservices-488523.iam.gserviceaccount.com.json"
    )
    assert output_file.exists()
    assert read_json(output_file) == expected


def test_write_evidence_files_routes_principals_to_type_directories(tmp_path: Path) -> None:
    grouped = read_fixture("grouped_routes.json")

    write_evidence_files(tmp_path, "example-project", grouped)

    assert (tmp_path / "by_principal" / "user" / "alice_example.com.json").exists()
    assert (tmp_path / "by_principal" / "group" / "eng_example.com.json").exists()
    assert (
        tmp_path
        / "by_principal"
        / "serviceAccount"
        / "svc_example.iam.gserviceaccount.com.json"
    ).exists()


def test_write_evidence_files_skips_unsupported_principal_types(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    grouped = read_fixture("grouped_unsupported.json")

    with caplog.at_level(logging.WARNING):
        write_evidence_files(tmp_path, "example-project", grouped)

    assert "Skipping unsupported principal format: domain:example.com" in caplog.text
    assert not list((tmp_path / "by_principal").rglob("*.json"))


def test_write_evidence_files_keeps_filename_sanitization(tmp_path: Path) -> None:
    grouped = read_fixture("grouped_sanitization.json")

    write_evidence_files(tmp_path, "example-project", grouped)

    assert (tmp_path / "by_principal" / "user" / "theampersand_dev_gmail.com.json").exists()
