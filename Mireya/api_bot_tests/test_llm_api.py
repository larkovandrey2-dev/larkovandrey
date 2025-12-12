import sys
import os
import unittest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["SUPABASE_URL"] = "https://example.com"
os.environ["SUPABASE_SERVICE_KEY"] = "fake_key"
os.environ["ADMINS"] = "123"

mock_db_module = MagicMock()
mock_db_module.DatabaseService = MagicMock()
sys.modules["helpers.database"] = mock_db_module

mock_llm_interaction = MagicMock()
mock_llm_interaction.analyze_question = AsyncMock()
sys.modules["llm_service"] = MagicMock()
sys.modules["llm_service.interaction"] = mock_llm_interaction

try:
    from main import app

    PATCH_TARGET = "main.llm.analyze_question"
except ImportError:
    from api.main import app

    PATCH_TARGET = "api.main.llm.analyze_question"


class TestMireyaAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        json_path = os.path.join(current_dir, 'jsn_test.json')
        if not os.path.exists(json_path):
            json_path = os.path.join(current_dir, 'data', 'jsn_test.json')

        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                self.test_cases = json.load(f)
        else:
            self.test_cases = []

    def test_scenarios(self):
        if not self.test_cases:
            self.skipTest("JSON not found")

        with patch(PATCH_TARGET, new_callable=AsyncMock) as mock_analyze:
            for case in self.test_cases:
                with self.subTest(msg=case['name']):
                    mock_analyze.return_value = case['mock_llm_return']

                    response = self.client.post("/api/generate", json=case['input'])

                    self.assertEqual(response.status_code, case['expected_status'])
                    self.assertEqual(response.json(), case['expected_response'])


if __name__ == '__main__':
    unittest.main()