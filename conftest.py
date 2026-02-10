from pathlib import Path

from tally.config import load_from_file

# Load test config before any test (or module that uses config) runs
load_from_file(Path(__file__).resolve().parent / "tests" / "tally" / "fixtures" / "config.yaml")

from tests.tally.mocks.mock_db import mock_db
