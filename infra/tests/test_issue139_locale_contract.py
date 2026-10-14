"""Reject obvious English validation literals on customer runtime paths."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2] / "app/centrochange_core/centrochange_core"
LITERAL = re.compile(r"frappe\.throw\(\s*(['\"])(.*?)\1", re.S)
ENGLISH = re.compile(r"\b(?:the|an|and|must|requires|cannot|only|choose|invalid|unsupported|"
                     r"missing|failed|access|permission|different|review|source|payload|request|"
                     r"records|center|narrow)\b", re.I)


class CustomerValidationLocaleTests(unittest.TestCase):
    def test_customer_throw_literals_are_not_obviously_english(self):
        remaining = []
        for path in ROOT.rglob("*.py"):
            relative = str(path.relative_to(ROOT))
            if relative.startswith("uat/") or path.name in {
                "dev_acceptance.py", "dev_bootstrap.py", "incoming_acceptance.py",
                "banking_acceptance.py", "receivables_acceptance.py",
            }:
                continue
            for match in LITERAL.finditer(path.read_text()):
                message = match.group(2)
                if ENGLISH.search(message) and "example.invalid" not in message:
                    remaining.append((relative, message))
        self.assertEqual(remaining, [])
