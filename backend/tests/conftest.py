"""Point the test suite at a throwaway database.

`app.db.database` resolves its engine at import time, so DATABASE_URL has to be
set before the app package is imported. Without this the suite writes its
fixture projects and brand plans into the developer's real brandplan.db.
"""
import os
import tempfile

_TEST_DB = os.path.join(tempfile.mkdtemp(prefix="brandplan-tests-"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ.setdefault("APP_ENV", "test")
