from pathlib import Path


"""Return project root folder."""
DEFAULT_PATH = Path(__file__).resolve().parent.parent

"""Return config folder."""
DEFAULT_CONFIG_PATH = DEFAULT_PATH / "config"

"""Return media folder."""
DEFAULT_FILE_PATH = DEFAULT_PATH / "media"

"""Return message_history folder."""
DEFAULT_MESSAGE_PATH = DEFAULT_PATH / "message"


