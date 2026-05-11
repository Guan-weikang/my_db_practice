from pathlib import Path
import os
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:123456@localhost:5432/family_tree_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
