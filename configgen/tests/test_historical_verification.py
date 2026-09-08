import yaml
from conftest import REPO_ROOT, TOPOLOGY_DIR

from avionics_configgen.cli import main


def test_verify_matches_real_captured_facts():
    exit_code = main(
        [
            "verify",
            str(TOPOLOGY_DIR / "avionics-real.yaml"),
            "--reference",
            str(REPO_ROOT / "validation" / "historical-addressing.yaml"),
        ]
    )
    assert exit_code == 0


def test_verify_detects_a_real_mismatch(tmp_path):
    """The check must not be vacuous -- prove it actually fails when the
    reference and the generator disagree.
    """
    reference_path = REPO_ROOT / "validation" / "historical-addressing.yaml"
    with open(reference_path, encoding="utf-8") as f:
        reference = yaml.safe_load(f)

    reference["vlans"]["10"]["gateway"] = "192.168.10.99"  # deliberately wrong

    corrupted_path = tmp_path / "corrupted-reference.yaml"
    with open(corrupted_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(reference, f)

    exit_code = main(
        [
            "verify",
            str(TOPOLOGY_DIR / "avionics-real.yaml"),
            "--reference",
            str(corrupted_path),
        ]
    )
    assert exit_code == 1
