from pathlib import Path


"""Return project root folder."""
DEFAULT_PATH = Path(__file__).resolve().parent.parent

"""Return config folder."""
DEFAULT_CONFIG_PATH = DEFAULT_PATH / "config"
if not Path(DEFAULT_CONFIG_PATH).is_dir():
    Path(DEFAULT_CONFIG_PATH).mkdir(exist_ok=True)

"""Return data folder."""
DEFAULT_DATA_PATH = DEFAULT_PATH / "data"
if not Path(DEFAULT_DATA_PATH).is_dir():
    Path(DEFAULT_DATA_PATH).mkdir(exist_ok=True)


