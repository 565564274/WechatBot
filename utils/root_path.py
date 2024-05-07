from pathlib import Path


"""Return project root folder."""
DEFAULT_PATH = Path(__file__).resolve().parent.parent

"""Return config folder."""
DEFAULT_CONFIG_PATH = DEFAULT_PATH / "config"

"""Return temp folder."""
DEFAULT_TEMP_PATH = DEFAULT_PATH / "temp" / "project"


