import os
import pytest

os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost:5432/dna_db_test"
