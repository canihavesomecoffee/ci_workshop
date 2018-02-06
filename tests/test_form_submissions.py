import ci_demo
from tests import base


class TestFormSubmissions(base.BaseTestCase):
    render_templates = False

    def test_that_new_user_is_created_when_account_does_not_yet_exist(self):
        self.assertEqual(0, len(ci_demo.User.query.all()))
        with self.app.test_client() as c:
            c.post('/login', data=dict(name="test", password="test", submit=True))
        self.assertEqual(1, len(ci_demo.User.query.all()))

    def test_that_user_gets_error_message_when_wrong_credentials_entered(self):
        u = self.create_user()
        self.assertEqual(1, len(ci_demo.User.query.all()))
        with self.app.test_client() as c:
            c.post('/login', data=dict(name=u.name, password="wrong", submit=True))
            self.assertMessageFlashed('Wrong username or password', 'error-message')
        self.assertEqual(1, len(ci_demo.User.query.all()))

    def test_that_user_session_is_set_on_successful_login(self):
        u = self.create_user()
        self.assertEqual(1, len(ci_demo.User.query.all()))
        with self.app.test_client() as c:
            import flask
            c.post('/login', data=dict(name=u.name, password="test", submit=True))
            self.assertEqual(flask.session.get('user_id', 0), u.id)
        self.assertEqual(1, len(ci_demo.User.query.all()))

    def test_that_user_is_redirected_to_index_when_no_next_step_was_specified(self):
        u = self.create_user()
        with self.app.test_client() as c:
            r = c.post('/login', data=dict(name=u.name, password="test", submit=True))
            self.assertRedirects(r, '/')

    def test_that_user_is_redirected_to_correct_page_when_next_step_was_specified(self):
        u = self.create_user()
        with self.app.test_client() as c:
            r = c.post('/login?next=my_workshop', data=dict(name=u.name, password="test", submit=True))
            self.assertRedirects(r, '/my_workshop')
