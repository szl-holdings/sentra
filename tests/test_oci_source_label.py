#!/usr/bin/env python3
"""Offline OCI source contract; does not prove GHCR package write access."""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_LABEL = (
    'LABEL org.opencontainers.image.source="https://github.com/szl-holdings/sentra"'
)


def check_declaration(dockerfile: str, workflow: str) -> None:
    labels = [
        line.strip()
        for line in dockerfile.splitlines()
        if re.match(r"^\s*LABEL\s+org\.opencontainers\.image\.source\b", line)
    ]
    if labels != [SOURCE_LABEL]:
        raise AssertionError("OCI source must uniquely identify the sentra repository")
    if not re.search(r"(?m)^\s+packages:\s*write\s*$", workflow):
        raise AssertionError("GHCR job must explicitly request packages: write")
    if not re.search(r"(?m)^\s+id-token:\s*write\s*$", workflow):
        raise AssertionError("GHCR attestation job must explicitly request OIDC")


class SourceLabelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        cls.workflow = (
            ROOT / ".github" / "workflows" / "ghcr-build-push.yml"
        ).read_text(encoding="utf-8")

    def test_exact_oci_source_and_permissions(self) -> None:
        check_declaration(self.dockerfile, self.workflow)

    def test_unlabeled_image_refused(self) -> None:
        with self.assertRaises(AssertionError):
            check_declaration(self.dockerfile.replace(SOURCE_LABEL, ""), self.workflow)

    def test_wrong_repository_refused(self) -> None:
        with self.assertRaises(AssertionError):
            check_declaration(
                self.dockerfile.replace(
                    SOURCE_LABEL, SOURCE_LABEL.replace("sentra", "rosie")
                ),
                self.workflow,
            )

    def test_duplicate_source_label_refused(self) -> None:
        with self.assertRaises(AssertionError):
            check_declaration(
                self.dockerfile + "\n" + SOURCE_LABEL + "\n", self.workflow
            )

    def test_package_write_permission_absence_refused(self) -> None:
        with self.assertRaises(AssertionError):
            check_declaration(
                self.dockerfile,
                self.workflow.replace("packages: write", "packages: read"),
            )

    def test_oidc_permission_absence_refused(self) -> None:
        with self.assertRaises(AssertionError):
            check_declaration(
                self.dockerfile,
                self.workflow.replace("id-token: write", "id-token: read"),
            )


if __name__ == "__main__":
    unittest.main()
