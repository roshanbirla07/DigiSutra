import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import configuration.variables as variables


class StaticConfigurationTests(unittest.TestCase):
    def test_instance_config_overrides_static_defaults(self):
        instance_config = types.ModuleType("configuration.instance_config")
        instance_config.AWS_REGION = "eu-west-1"
        instance_config.AWS_S3_BUCKET_NAME = "instance-bucket"

        try:
            with patch.dict(sys.modules, {"configuration.instance_config": instance_config}):
                reloaded = importlib.reload(variables)
                self.assertEqual(reloaded.AWS_REGION, "eu-west-1")
                self.assertEqual(reloaded.AWS_S3_BUCKET_NAME, "instance-bucket")
        finally:
            sys.modules.pop("configuration.instance_config", None)
            importlib.reload(variables)

    def test_environment_does_not_override_static_configuration(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}):
            reloaded = importlib.reload(variables)
            self.assertEqual(reloaded.AWS_REGION, "ap-south-1")


if __name__ == "__main__":
    unittest.main()
