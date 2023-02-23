import unittest
import datetime as dt
import json
from async_chat import jim


class TestServerSchemas(unittest.TestCase):
    def setUp(self) -> None:
        self.current_datetime = dt.datetime.now(
            dt.timezone.utc
        )
        self.account_name = 'Ivan'
        self.password = 'ivan123'
        self.current_user = dict(
            account_name=self.account_name,
            password=self.password
        )

    def test_required_status_codes(self):
        required_codes = [
            100,
            200,
            201,
            202,
            400,
            404
        ]
        exist_codes = [code.value for code in list(jim.StatusCodes)]
        for required_code in required_codes:
            with self.subTest(required_code=required_code):
                self.assertIn(
                    required_code,
                    exist_codes
                )

    def test_message_alert(self):
        model_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_404_NOT_FOUND,
            alert='test_alert'
        )
        target_message = dict(
            response=jim.StatusCodes.HTTP_404_NOT_FOUND,
            time=model_message.time.timestamp(),
            alert='test_alert'
        )
        self.assertEqual(
            json.loads(model_message.json()),
            target_message
        )

    def test_message_error(self):
        model_message = jim.MessageError(
            response=jim.StatusCodes.HTTP_404_NOT_FOUND,
            error='test_error'
        )
        target_message = dict(
            response=jim.StatusCodes.HTTP_404_NOT_FOUND,
            time=model_message.time.timestamp(),
            error='test_error'
        )
        self.assertEqual(
            json.loads(model_message.json()),
            target_message
        )
