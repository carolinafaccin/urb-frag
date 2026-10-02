"""Figure style: the brand (brand.py, synced from the lina-brand repository) plus this
repository's source line. Colors, palettes and helpers come from brand.py; edit them there."""
from . import brand
from .brand import *  # noqa: F401,F403  colors, data palettes, header, scalebar, halo, save...
from .config import ROOT

SOURCE = "Source: Faccin (2025), thesis dataset on Zenodo (City of Santa Cruz do Sul, IBGE, MapBiomas, OpenStreetMap)."
REPO = "github.com/carolinafaccin/urb-frag"


def setup():
    """Register the bundled fonts (OFL) and set the matplotlib defaults."""
    brand.setup(ROOT / "assets" / "fonts")


def footer(fig, note=SOURCE):
    brand.footer(fig, note, REPO)
