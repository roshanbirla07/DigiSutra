import os
import sys
import unittest
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from configuration.db_routing import session_rollback


class SessionRollbackTests(unittest.TestCase):
    def test_integrity_failure_rolls_back_transaction(self):
        db = MagicMock()

        @session_rollback(db)
        def write():
            raise IntegrityError("insert", {}, Exception("duplicate"))

        with self.assertRaises(IntegrityError):
            write()
        db.session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
