"""The historical metadata producer must reproduce every non-validity field."""
import importlib,json,subprocess,sys
from pathlib import Path
import pytest
T=importlib.import_module("tools.20r2_9_backfill_validity")
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize("kind,name",[("hygiene","hygiene_checks"),("grid","realizability_grid")])
def test_historical_producer_cli(kind,name,tmp_path):
    out=tmp_path/"replay.json"
    subprocess.run([sys.executable,"-m","tools.20r2_9_regenerate_legacy_metadata","--kind",kind,"--out",str(out)],cwd=ROOT,check=True,capture_output=True)
    original=ROOT/"results/PENDING/phase-T2"/(name+".json")
    assert T.scientific_bytes(out.read_bytes())==T.scientific_bytes(original.read_bytes())
    assert json.loads(out.read_text())["validity"]==json.loads(original.read_text())["validity"]
