"""The pipeline must reproduce the numbers published in the thesis (needs the dataset; skipped without config)."""
import pytest

from urbfrag import config, data, metrics

CFG = config.ROOT / "config" / "config.local.json"
pytestmark = pytest.mark.skipif(not CFG.exists(), reason="config/config.local.json not set")


def test_published_numbers():
    dataset_dir, raw_dir, _ = config.load()
    data.fetch_dataset(dataset_dir)
    t = data.load_index(raw_dir)
    t = metrics.fragmentation_index(t) if t is not None else None
    val = metrics.validate(t, metrics.urban_growth(data.urban_area(dataset_dir)), data.developments(dataset_dir))
    if t is None:
        val = val[val["check"] != "index_min"]
    assert val["ok"].all(), val[~val["ok"]].to_string()
