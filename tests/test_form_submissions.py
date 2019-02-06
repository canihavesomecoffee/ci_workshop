from typing import Optional

import ci_demo
from tests import base


class TestLoginSubmissions(base.BaseTestCase):
    render_templates = False

    def create_login_form_data(self, password: Optional[str] = None) -> dict:
        """
        Creates the form data for a login event.

        :return: A dictionary containing the name, password and submit fields.
        """
        if password is None:
            password = self.user_password

        return {'name': self.user_name, 'password': password, 'submit': True}

    def test_that_new_user_is_created_when_account_does_not_yet_exist(self):
        self.assertEqual(0, len(ci_demo.User.query.all()))
        with self.app.test_client() as c:
            c.post('/login', data=self.create_login_form_data())
        self.assertEqual(1, len(ci_demo.User.query.all()))

    def test_that_user_gets_error_message_when_wrong_credentials_entered(self):
        self.create_user()
        self.assertEqual(1, len(ci_demo.User.query.all()))
        with self.app.test_client() as c:
            c.post('/login', data=self.create_login_form_data("wrong"))
            self.assertMessageFlashed('Wrong username or password', 'error-message')
        self.assertEqual(1, len(ci_demo.User.query.all()))

    def test_that_user_session_is_set_on_successful_login(self):
        self.create_user()
        self.assertEqual(1, len(ci_demo.User.query.all()))
        with self.app.test_client() as c:
            import flask
            c.post('/login', data=self.create_login_form_data())
            self.assertEqual(flask.session.get('user_id', 0), self.user_id)
        self.assertEqual(1, len(ci_demo.User.query.all()))

    def test_that_user_is_redirected_to_index_when_no_next_step_was_specified(self):
        self.create_user()
        with self.app.test_client() as c:
            r = c.post('/login', data=self.create_login_form_data())
            self.assertRedirects(r, '/')

    def test_that_user_is_redirected_to_correct_page_when_next_step_was_specified(self):
        self.create_user()
        with self.app.test_client() as c:
            r = c.post('/login?next=my_workshop', data=self.create_login_form_data())
            self.assertRedirects(r, '/my_workshop')


class TestWorkshopSubmissions(base.BaseTestCase):
    render_templates = False
    form_next = {'next': True}
    form_previous = {'previous': True}

    def assert_progress_of_workshop(self, initial_step: int, expected_step: int, form_data: dict) -> None:
        """
        Checks that if a request is made to change the progress of the workshop, the step is as expected.

        :param initial_step: The initial step to start from.
        :param expected_step: The expected step we should be at after the request.
        :param form_data: The form data used to change the workshop progress.
        :return: Nothing.
        """
        with self.app.test_client() as c:
            u = self.create_user_and_store_in_session(c)
            self.set_workshop_step_for_user(u, initial_step)

            c.post('/my_workshop', data=form_data)

            u = self.create_user()
            self.assertEqual(expected_step, u.workshop_step)

    def test_that_user_can_progress_to_next_workshop_step(self):
        self.assert_progress_of_workshop(1, 2, self.form_next)

    def test_that_user_can_return_to_the_previous_step(self):
        self.assert_progress_of_workshop(2, 1, self.form_previous)

    def test_that_user_cannot_go_back_further_than_the_first_step(self):
        self.assert_progress_of_workshop(1, 1, self.form_previous)

    def test_that_user_cannot_go_past_the_last_step(self):
        max_steps = len(ci_demo.workshop_steps)
        self.assert_progress_of_workshop(max_steps, max_steps, self.form_next)


class TestRequestHintSubmissions(base.BaseTestCase):
    render_templates = False

    def test_that_a_hint_can_be_retrieved_for_a_step_with_hints(self):
        with self.app.test_client() as c:
            u = self.create_user_and_store_in_session(c)
            self.set_workshop_step_for_user(u, 1)

            response = c.post('/my_workshop/hint')
            self.assertNotEquals(response.json, dict(error="No hints available"))

    def test_that_no_hint_can_be_retrieved_for_a_step_with_no_hints_left(self):
        with self.app.test_client() as c:
            u = self.create_user_and_store_in_session(c)
            self.set_workshop_step_for_user(u, 1)
            # Exhaust hints
            ci_demo.unlock_all_hints_for_step(1, u, ci_demo.workshop_hints)

            response = c.post('/my_workshop/hint')
            self.assertEquals(response.json, dict(error="No hints available"))

    def test_that_no_hint_can_be_retrieved_for_an_invalid_step(self):
        with self.app.test_client() as c:
            u = self.create_user_and_store_in_session(c)
            self.set_workshop_step_for_user(u, len(ci_demo.workshop_steps) + 1)

            response = c.post('/my_workshop/hint')
            self.assertEquals(response.json, dict(error="No hints available"))
