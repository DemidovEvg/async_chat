import unittest
import datetime as dt
import json
from async_chat import jim


class TestClientSchemas(unittest.TestCase):
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

    def test_get_right_datetime(self):
        model_message = jim.MessageUserAuth(
            user=self.current_user
        )
        almost_model_create_datetime = dt.datetime.now(dt.timezone.utc)
        self.assertAlmostEqual(
            model_message.time,
            almost_model_create_datetime
        )

    def test_client_actions(self):
        self.assertEqual(
            jim.ClientActions.presence.value,
            'presense'
        )
        self.assertEqual(
            jim.ClientActions.quit.value,
            'quit'
        )
        self.assertEqual(
            jim.ClientActions.msg.value,
            'msg'
        )
        self.assertEqual(
            jim.ClientActions.authenticate.value,
            'authenticate'
        )
        self.assertEqual(
            jim.ClientActions.join_.value,
            'join'
        )
        self.assertEqual(
            jim.ClientActions.leave.value,
            'leave'
        )

    def test_client_statuses(self):
        self.assertEqual(
            jim.Statuses.i_am_here.value,
            'Yep, I am here!'
        )

    def test_message_user_auth(self):
        model_message = jim.MessageUserAuth(
            user=self.current_user
        )
        target_message = dict(
            action=jim.ClientActions.authenticate.value,
            time=model_message.time.timestamp(),
            user=dict(
                account_name=self.account_name,
                password=self.password
            )
        )
        self.assertEqual(
            json.loads(model_message.json()),
            target_message
        )

    def test_message_user_presence(self):
        model_message = jim.MessageUserPresence(
            user=self.current_user
        )
        target_message = dict(
            action=jim.ClientActions.presence.value,
            time=model_message.time.timestamp(),
            user=dict(
                account_name=self.account_name,
                status=jim.Statuses.i_am_here
            )
        )
        self.assertEqual(
            json.loads(model_message.json()),
            target_message
        )

    def test_message_user_quit(self):
        model_message = jim.MessageUserQuit(
            user=self.current_user
        )
        target_message = dict(
            action=jim.ClientActions.quit.value,
            time=model_message.time.timestamp(),
            user=dict(
                account_name=self.account_name
            )
        )
        self.assertEqual(
            json.loads(model_message.json()),
            target_message
        )
