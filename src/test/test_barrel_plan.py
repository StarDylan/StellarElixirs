### Tests ###
from fastapi.testclient import TestClient
from ..api.server import app
import sys
sys.path.append(".")

client = TestClient(app)