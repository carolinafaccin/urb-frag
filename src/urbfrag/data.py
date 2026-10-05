"""Load the thesis dataset (Zenodo) and the fragmentation-index variables."""
import urllib.request

import geopandas as gpd
import pandas as pd

from .config import CD_MUN, CRS, DATASET_FILES, INDEX, STATE, ZENODO_RECORD

YEARS = [1985, 1993, 2013, 2022]
# Phases of the thesis
PHASES = {"1970–1993": (1970, 1993), "1993–2013": (1994, 2013), "2013–2022": (2014, 2022)}

# The 23 variables of the index (thesis, Quadro 4.5), by tract: score column -> (label, dimension)
VARIABLES = {
    "v13": ("Permanent preservation areas (%)", "Environmental"),
    "v14": ("Landslide-prone area (%)", "Environmental"),
    "v15": ("Dwellings in flood areas (%)", "Environmental"),
    "v01": ("Population density", "Social"),
    "v02": ("Commercial establishments (%)", "Social"),
    "v03": ("Schools", "Social"),
    "v04": ("Dwellings within 1 km of a health post (%)", "Social"),
    "v05": ("White population (%)", "Social"),
    "v06": ("Residents per dwelling", "Social"),
    "v07": ("Households above 10 minimum wages per capita (%)", "Social"),
    "v08": ("Households up to 1 minimum wage per capita (%)", "Social"),
    "v11": ("Dwellings in informal settlements (%)", "Social"),
    "v12": ("Dwellings in special social-interest zones (%)", "Social"),
    "v16": ("High-standard buildings (%)", "Housing"),
    "v17": ("Simple-standard buildings (%)", "Housing"),
    "v18": ("Low-cost buildings (%)", "Housing"),
    "v21": ("Dwellings in social housing subdivisions (%)", "Housing"),
    "v22": ("Dwellings in gated communities (%)", "Housing"),
    "v19": ("Dwellings built in the last 5 years (%)", "Infrastructure"),
    "v20": ("Dwellings older than 30 years (%)", "Infrastructure"),
    "v23": ("Street length", "Infrastructure"),
    "v24": ("Dwellings with water supply (%)", "Infrastructure"),
    "v25": ("Bus lines", "Infrastructure"),
}
# Raw values shown on the indicator maps
RAW = {"v07_renda1": "v07", "v08_rendam": "v08", "v12_zeis": "v12", "v22_condfe": "v22", "v21_lotpop": "v21", "v14_desl": "v14"}


def fetch_dataset(dataset_dir):
    """Download the thesis dataset from Zenodo into dataset_dir when files are missing."""
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for name in DATASET_FILES:
        dest = dataset_dir / name
        if dest.exists():
            continue
        url = f"https://zenodo.org/records/{ZENODO_RECORD}/files/{name}?download=1"
        print(f"downloading {name} from Zenodo")
        req = urllib.request.Request(url, headers={"User-Agent": "urb-frag (github.com/carolinafaccin/urb-frag)"})
        with urllib.request.urlopen(req, timeout=300) as r:
            dest.write_bytes(r.read())


def layer(dataset_dir, gpkg, name):
    g = gpd.read_file(dataset_dir / f"{gpkg}.gpkg", layer=name).to_crs(CRS)
    g["geometry"] = g.geometry.force_2d()
    return g


def urban_area(dataset_dir):
    """MapBiomas urbanized area of the municipal seat, 1985, 1993, 2013 and 2022."""
    out = []
    for y in YEARS:
        g = layer(dataset_dir, "dados_mapbiomas", f"scs_area-urbanizada-sede_{y}_pol")
        out.append(gpd.GeoDataFrame({"year": [y]}, geometry=[g.union_all()], crs=CRS))
    return pd.concat(out, ignore_index=True)


def developments(dataset_dir):
    """Gated communities and social housing subdivisions approved by the City, with their year."""
    gated = layer(dataset_dir, "dados_prefeitura_loteamentos", "scs_condominios-fechados_2022_pol")
    gated = gated[~gated["nome"].str.contains("cancelado", case=False, na=False)].assign(kind="Gated community")
    # Despite its name, this layer holds the social housing (popular and COHAB) subdivisions
    social = layer(dataset_dir, "dados_prefeitura_loteamentos", "scs_loteamentos-fechados_2022_pol").assign(kind="Social housing")
    d = pd.concat([gated, social], ignore_index=True)[["nome", "kind", "uso", "ano", "geometry"]]
    d["year"] = d["ano"].astype("Int64")
    d["phase"] = pd.cut(d["year"].astype(float), [1969, 1993, 2013, 2022], labels=list(PHASES))
    d["area_km2"] = d.area / 1e6
    return gpd.GeoDataFrame(d, crs=CRS)


def context(dataset_dir):
    """Layers drawn on the maps."""
    pd_ = layer(dataset_dir, "dados_prefeitura", "scs_plano-diretor_2019_pol")
    return {
        "municipality": layer(dataset_dir, "dados_ibge", "scs_municipio_2022_pol"),
        "urban_2016": layer(dataset_dir, "dados_prefeitura", "scs_area-urbana_2016_pol"),
        "neighborhoods": layer(dataset_dir, "dados_prefeitura", "scs_bairros_pol"),
        "highways": layer(dataset_dir, "dados_openstreetmap", "scs_rodovias_2024_lin"),
        "streets": layer(dataset_dir, "dados_openstreetmap", "scs_eixos-viarios_2024_lin"),
        "industrial": pd_[pd_["name1_"].eq("Zona Industrial")],
        "green_belt": layer(dataset_dir, "dados_prefeitura", "scs_app_cinturao-verde_pol"),
        "water": layer(dataset_dir, "dados_prefeitura", "scs_hidrografia_pol"),
    }


def load_index(sources_dir):
    """Scored variables (20 to 100) by 2010 census tract. None if sources_dir does not have them."""
    if sources_dir is None or not (sources_dir / INDEX).exists():
        return None
    g = gpd.read_file(sources_dir / INDEX).to_crs(CRS)
    g = g[g[list(VARIABLES)].notna().all(axis=1)].copy()
    return g.rename(columns={"cd_geocodi": "tract", "nm_bairro": "neighborhood"})


def load_state(sources_dir):
    if sources_dir is None or not (sources_dir / STATE).exists():
        return None
    s = gpd.read_file(sources_dir / STATE).to_crs(CRS)
    s["is_scs"] = s["CD_MUN"].eq(CD_MUN)
    return s
