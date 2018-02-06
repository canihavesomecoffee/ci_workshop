from unittest import mock, TestCase
from tests import base


class TestLoginRequiredWrapper(TestCase):
    def test_that_login_required_does_not_redirect_when_logged_in(self):
        with mock.patch('flask.g') as m_g:
            from ci_demo import app, User
            m_g.user = User()
            with app.test_request_context('/my_workshop'):
                from ci_demo import login_required

                wrapped_def = mock.MagicMock()
                wrapper = login_required(wrapped_def)

                wrapper()

                wrapped_def.assert_called_once()

    def test_that_login_required_redirects_to_login_when_not_logged_in(self):
        with mock.patch('flask.g') as m_g:
            m_g.user = None
            from ci_demo import app
            with app.test_request_context('/my_workshop'):
                from flask import url_for
                from ci_demo import login_required

                wrapped_def = mock.MagicMock()
                wrapper = login_required(wrapped_def)

                rv = wrapper()

                wrapped_def.assert_not_called()
                self.assertEqual(rv.status_code, 302)
                self.assertEqual(rv.location, url_for('login', next='my_workshop'))


class TestGlobalContext(base.BaseTestCase):
    def test_that_none_is_added_as_user_to_the_global_context_when_there_is_no_session_id(self):
        with mock.patch('flask.g') as m_g:
            with self.app.test_request_context('/my_workshop'):
                import flask
                self.assertEqual(flask.session.get('user_id', 0), 0)

                self.app.preprocess_request()

                self.assertIsNone(m_g.user)

    def test_that_the_user_is_added_to_the_global_context(self):
        with mock.patch('flask.g') as m_g:
            with self.app.test_client() as c:
                u = self.create_user_and_store_in_session(c)
                c.get('/workshop')
                self.assertEqual(m_g.user, u)
