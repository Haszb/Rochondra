import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import toml as tomllib

ROOT_DIR = Path(__file__).resolve().parent.parent

TOML_PATH = ROOT_DIR / "config.toml"

if not TOML_PATH.exists():
    raise FileNotFoundError(f"Le fichier de configuration global est introuvable à l'emplacement : {TOML_PATH}")

with open(TOML_PATH, "rb") as f:
    _config_data = tomllib.load(f)


STORAGE_ROOT = ROOT_DIR / _config_data["global"]["storage_base_dir"]
print(f"STORAGE_ROOT is set to: {STORAGE_ROOT}")

class WhitepaperConfig:
    """Hub de configuration dédié au module Whitepaper"""
    _wp = _config_data["whitepaper"]
    
    # Chemins absolus résolus sous forme d'objets Path
    PDF_DIR = STORAGE_ROOT / _wp["pdf_subdir"]
    MD_DIR = STORAGE_ROOT / _wp["markdown_subdir"]
    IMG_DIR = STORAGE_ROOT / _wp["images_subdir"]
    REGISTRY_PATH = STORAGE_ROOT / "index_registry.csv"

class TokenomicsConfig:
    pass

def init_storage_directories():
    """Crée tous les dossiers de stockage s'ils n'existent pas sur la machine"""
    directories = [
        WhitepaperConfig.PDF_DIR,
        WhitepaperConfig.MD_DIR,
        WhitepaperConfig.IMG_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)