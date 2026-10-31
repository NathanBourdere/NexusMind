import subprocess
import sys


def test_import_has_no_infrastructure_side_effects():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import nexusmind; import sys; "
            "assert 'sentence_transformers' not in sys.modules; "
            "assert 'requests' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
