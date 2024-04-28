import sys
import uvicorn
from fast_api.fast_api import app
from utils import resource_pool

host = "127.0.0.1" if "win" in sys.platform else "0.0.0.0"
uvicorn.run(app=app, host=host, port=resource_pool["port"] if "port" in resource_pool else 9981)


