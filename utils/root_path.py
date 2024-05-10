from pathlib import Path


"""Return project root folder."""
DEFAULT_PATH = Path(__file__).resolve().parent.parent

"""Return config folder."""
DEFAULT_CONFIG_PATH = DEFAULT_PATH / "config"
if not Path(DEFAULT_CONFIG_PATH).is_dir():
    Path(DEFAULT_CONFIG_PATH).mkdir(exist_ok=True)


