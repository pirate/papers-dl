"""Integration tests against real publisher and NLM open-access services."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


class TestOpenAccessCLI(unittest.TestCase):
    def fetch_paper(self, identifier, provider, expected_text, expected_source):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run(
                [
                    sys.executable,
                    "src/papers_dl.py",
                    "--verbose",
                    "fetch",
                    "--providers",
                    provider,
                    "--output",
                    output,
                    identifier,
                ],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Successfully downloaded", result.stdout, result.stderr)
            self.assertIn(expected_source, result.stdout)
            files = list(Path(output).glob("*.pdf"))
            self.assertEqual(len(files), 1, result.stdout)
            self.assertTrue(files[0].read_bytes().startswith(b"%PDF-"))
            with fitz.open(files[0]) as paper:
                self.assertGreater(paper.page_count, 0)
                self.assertIn(expected_text, paper[0].get_text())

    def test_default_provider_downloads_open_access_doi(self):
        self.fetch_paper(
            "10.1126/sciadv.1602552",
            "all",
            "Microbial arms race",
            "https://pmc-oa-opendata.s3.amazonaws.com/",
        )

    def test_pmc_resolves_doi_url(self):
        self.fetch_paper(
            "https://doi.org/10.1126/sciadv.1602552",
            "pmc",
            "Microbial arms race",
            "https://pmc-oa-opendata.s3.amazonaws.com/",
        )

    def test_publisher_resolves_doi(self):
        self.fetch_paper(
            "10.21105/joss.01112",
            "publisher",
            "HRDS",
            "https://joss.theoj.org/papers/10.21105/joss.01112.pdf",
        )

    def test_publisher_resolves_landing_page(self):
        self.fetch_paper(
            "https://joss.theoj.org/papers/10.21105/joss.01112",
            "publisher",
            "HRDS",
            "https://joss.theoj.org/papers/10.21105/joss.01112.pdf",
        )

    def test_publisher_discovers_pdf_without_pdf_extension(self):
        self.fetch_paper(
            "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0185809",
            "publisher",
            "More than 75 percent decline",
            "https://journals.plos.org/plosone/article/file?",
        )

    def test_pmc_resolves_pubmed_id_for_another_journal(self):
        self.fetch_paper(
            "23193287",
            "pmc",
            "GenBank",
            "https://pmc-oa-opendata.s3.amazonaws.com/PMC3531190.1/",
        )

    def test_default_provider_accepts_pubmed_id(self):
        self.fetch_paper(
            "23193287",
            "all",
            "GenBank",
            "https://pmc-oa-opendata.s3.amazonaws.com/PMC3531190.1/",
        )

    def test_pmc_discovers_available_version_without_version_one(self):
        self.fetch_paper(
            "PMC1193645",
            "pmc",
            "Impaired Development",
            "https://pmc-oa-opendata.s3.amazonaws.com/PMC1193645.2/",
        )

    def test_pmc_honors_explicit_version(self):
        self.fetch_paper(
            "PMC1193645.2",
            "pmc",
            "Impaired Development",
            "https://pmc-oa-opendata.s3.amazonaws.com/PMC1193645.2/",
        )

    def test_pmc_does_not_substitute_an_unavailable_explicit_version(self):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run(
                [
                    sys.executable,
                    "src/papers_dl.py",
                    "--verbose",
                    "fetch",
                    "--providers",
                    "pmc",
                    "--output",
                    output,
                    "PMC1193645.1",
                ],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No papers found", result.stdout, result.stderr)
            self.assertEqual(list(Path(output).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
