import sys
import os
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Фейковые переменные
os.environ["SUPABASE_URL"] = "https://example.com"
os.environ["SUPABASE_SERVICE_KEY"] = "fake_key"
os.environ["ADMINS"] = "123"

# Подменяем модули
mock_db_module = MagicMock()
mock_db_service = MagicMock()
mock_db_module.DatabaseService = mock_db_service
sys.modules["helpers.database"] = mock_db_module
sys.modules["llm_service"] = MagicMock()
sys.modules["llm_service.interaction"] = MagicMock()

# Импортируем приложение и определяем пути для патчей
try:
    from main import app

    # Если импорт сработал, значит main в корне
    DB_PATCH_PATH = "main.db"
    app_module_path = "main"
except ImportError:
    from api.main import app

    # Если импорт сработал тут, значит main в папке api
    DB_PATCH_PATH = "api.main.db"
    app_module_path = "api.main"

class TestMireyaCRUD(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # --- ТЕСТЫ ПОЛЬЗОВАТЕЛЕЙ ---

    def test_register_new_user(self):
        """Тест регистрации НОВОГО пользователя"""
        user_id = 999

        with patch(f"{DB_PATCH_PATH}.get_all_users", new_callable=AsyncMock) as mock_get, \
                patch(f"{DB_PATCH_PATH}.create_user", new_callable=AsyncMock) as mock_create:
            mock_get.return_value = [100, 200]

            response = self.client.get(f"/api/register_user/{user_id}")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "created", "user_id": user_id, "role": "user"})
            mock_create.assert_awaited_once()

    def test_register_existing_user(self):
        """Тест регистрации СУЩЕСТВУЮЩЕГО пользователя"""
        user_id = 100

        with patch(f"{DB_PATCH_PATH}.get_all_users", new_callable=AsyncMock) as mock_get, \
                patch(f"{DB_PATCH_PATH}.create_user", new_callable=AsyncMock) as mock_create:
            mock_get.return_value = [100, 200]

            response = self.client.get(f"/api/register_user/{user_id}")

            self.assertEqual(response.json(), {"status": "exists", "user_id": user_id})
            mock_create.assert_not_awaited()

    def test_get_user_info(self):
        """Тест получения статистики пользователя"""
        user_id = 100
        fake_stats = {"role": "user", "age": 20, "surveys_count": 5}

        with patch(f"{DB_PATCH_PATH}.get_user_stats", new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = fake_stats

            response = self.client.get(f"/api/get_user/{user_id}")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), fake_stats)

    # --- ТЕСТЫ ОТВЕТОВ И РЕЗУЛЬТАТОВ ---

    def test_add_answer(self):
        """Тест сохранения ответа пользователя"""
        payload = {
            "user_id": 100,
            "survey_n": 1,
            "global_n": 10,
            "question_n": 1,
            "text": "Ответ пользователя",
            "date": "2023-01-01"
        }

        with patch(f"{DB_PATCH_PATH}.add_user_answer", new_callable=AsyncMock) as mock_add:
            response = self.client.post("/api/add_answer", json=payload)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})

            mock_add.assert_awaited_once_with(
                100, 10, 1, 1, "Ответ пользователя", "2023-01-01"
            )

    def test_add_survey_result(self):
        """Тест сохранения результата опроса"""
        payload = {
            "user_id": 100,
            "global_n": 10,
            "survey_n": 1,
            "date": "2023-01-01",
            "result": 50
        }

        with patch(f"{DB_PATCH_PATH}.add_survey_result", new_callable=AsyncMock), \
                patch(f"{DB_PATCH_PATH}.get_user_stats", new_callable=AsyncMock) as mock_stats, \
                patch(f"{DB_PATCH_PATH}.change_user_stat", new_callable=AsyncMock) as mock_change:
            mock_stats.return_value = {'surveys_count': 0, 'all_user_global_attempts': []}

            response = self.client.post("/api/add_survey_result", json=payload)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(mock_change.called)

    # --- ТЕСТЫ ВОПРОСОВ ---

    def test_add_question(self):
        """Тест добавления вопроса"""
        payload = {
            "user_id": 1,
            "survey_n": 1,
            "question_n": 5,
            "text": "Новый вопрос",
            "global_n": 0,
            "date": "now"
        }

        with patch(f"{DB_PATCH_PATH}.add_user_answer", new_callable=AsyncMock) as mock_add:
            response = self.client.post("/api/add_question", json=payload)
            self.assertEqual(response.status_code, 200)
            mock_add.assert_awaited()

    def test_delete_question(self):
        """Тест удаления вопроса"""
        payload = {"question_index": 5, "survey_index": 1}

        with patch(f"{DB_PATCH_PATH}.delete_question", new_callable=AsyncMock) as mock_del:
            response = self.client.post("/api/delete_question", json=payload)

            self.assertEqual(response.status_code, 200)
            mock_del.assert_awaited_once_with(5, 1)

    def test_get_questions_list(self):
        """Тест получения списка вопросов"""
        survey_id = 1
        fake_questions = [
            {"survey_index": 1, "text": "Q1"},
            {"survey_index": 2, "text": "Q2"}
        ]