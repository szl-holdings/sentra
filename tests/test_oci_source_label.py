#!/usr/bin/env python3
"""Offline OCI provenance guard; source checks do not grant GHCR write access."""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_LABEL = (
    'LABEL org.opencontainers.image.source="https://github.com/szl-holdings/sentra"'
)


def _publisher_job_permissions(workflow: str) -> dict[str, str]:
    """Read only the fixed-format build-push job, not comments or other jobs.

    This is a narrow fail-closed contract for this repository's workflow
    layout, not a general-purpose YAML parser. Unknown syntax must be reviewed.
    """
    lines = workflow.splitlines()
    starts = [i for i, line in enumerate(lines) if line == "  build-push:"]
    if len(starts) != 1:
        raise AssertionError("expected exactly one build-push job")
    start = starts[0]
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if re.fullmatch(r"  [A-Za-z][A-Za-z0-9_-]*:", lines[i])
        ),
        len(lines),
    )
    job = lines[start + 1 : end]
    if not any(
        line.lstrip().startswith("- uses: docker/build-push-action@") for line in job
    ):
        raise AssertionError("build-push job must contain the pinned publisher action")
    sections = [i for i, line in enumerate(job) if line == "    permissions:"]
    if len(sections) != 1:
        raise AssertionError("publisher job must declare its own permissions")
    permissions: dict[str, str] = {}
    for line in job[sections[0] + 1 :]:
        if re.match(r"^    [A-Za-z][A-Za-z0-9_-]*:", line):
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"      ([a-z][a-z-]*): (read|write|none)", line)
        if match is None or match.group(1) in permissions:
            raise AssertionError("unexpected publisher permission syntax")
        permissions[match.group(1)] = match.group(2)
    return permissions


def check_declaration(dockerfile: str, workflow: str) -> None:
    labels = [
        line.strip()
        for line in dockerfile.splitlines()
        if re.match(r"^\s*LABEL\s+org\.opencontainers\.image\.source\b", line)
    ]
    if labels != [SOURCE_LABEL]:
        raise AssertionError("OCI source must uniquely identify the sentra repository")
    permissions = _publisher_job_permissions(workflow)
    for needed in ("packages", "id-token"):
        if permissions.get(needed) != "write":
            raise AssertionError("build-push job missing required " + needed + " write")


class SourceLabelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        cls.workflow = (
            ROOT / ".github" / "workflows" / "ghcr-build-push.yml"
        ).read_text(encoding="utf-8")

    def test_exact_oci_source_and_job_scoped_permissions(self) -> None:
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

    def test_commented_out_permission_refused(self) -> None:
        tampered = self.workflow.replace(
            "      packages: write",
            "      packages: read\n      # packages: write",
        )
        with self.assertRaises(AssertionError):
            check_declaration(self.dockerfile, tampered)

    def test_permissions_in_unrelated_job_refused(self) -> None:
        tampered = (
            self.workflow.replace("      packages: write", "      packages: read")
            + "\n  unused-job:\n    permissions:\n      packages: write\n      id-token: write\n"
        )
        with self.assertRaises(AssertionError):
            check_declaration(self.dockerfile, tampered)

    def test_publishing_action_moved_out_of_job_refused(self) -> None:
        tampered = self.workflow.replace(
            "- uses: docker/build-push-action@", "- uses: actions/checkout@"
        )
        with self.assertRaises(AssertionError):
            check_declaration(self.dockerfile, tampered)


if __name__ == "__main__":
    unittest.main()
