"""Paths: read from config/config.local.json (gitignored), like the other repositories.

- dataset_dir  the thesis dataset (Zenodo). Downloaded there if the files are missing.
- raw_dir      shared raw-data catalog (index variables by census tract, state municipalities)
- data_dir     this project's outputs (tables, figures)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRS = 31982  # SIRGAS 2000 / UTM 22S

ZENODO_RECORD = "17025873"   # DOI 10.5281/zenodo.16423545 (all versions)
DATASET_FILES = ["dados_ibge.gpkg", "dados_mapbiomas.gpkg", "dados_openstreetmap.gpkg",
                 "dados_prefeitura.gpkg", "dados_prefeitura_loteamentos.gpkg"]

# Scored variables of the fragmentation index by 2010 census tract (the thesis' map-algebra input)
INDEX = "prefeituras_municipais/santa_cruz_do_sul/producao_carolina/scs_carolina/algebra_de_mapas/v_scs_algebra.shp"
STATE = "ibge/malha_municipal/2022/t0/RS_Municipios_2022.shp"
CD_MUN = "4316808"


def load():
    """Return (dataset_dir, raw_dir, data_dir); create data_dir subfolders."""
    cfg_path = ROOT / "config" / "config.local.json"
    if not cfg_path.exists():
        raise SystemExit(f"Missing {cfg_path.name}: copy config/config.local.json.example and set the folders.")
    cfg = json.loads(cfg_path.read_text())
    dataset_dir = Path(cfg["dataset_dir"])
    raw_dir = Path(cfg["raw_dir"]) if cfg.get("raw_dir") else None
    data_dir = Path(cfg["data_dir"])
    for sub in ("tables", "figures"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    return dataset_dir, raw_dir, data_dir
