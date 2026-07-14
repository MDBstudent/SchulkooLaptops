import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.server import extract_packages_from_winget_output


class ExtractPackagesTests(unittest.TestCase):
    def test_collects_package_ids_from_winget_output(self):
        sample_output = """Name                                      Id                           Version          Source
Microsoft Edge                             Microsoft.Edge               126.0.0          winget
Google Chrome                              Google.Chrome                126.0.0          winget
"""

        self.assertEqual(
            extract_packages_from_winget_output(sample_output),
            ["Google.Chrome", "Microsoft.Edge"],
        )


if __name__ == "__main__":
    unittest.main()
