from flask.testing import FlaskClient

import ci_demo
from ci_demo import app, db
from flask_testing import TestCase


class BaseTestCase(TestCase):
    user_id = 1
    user_name = 'test'
    user_password = 'test'

    def create_app(self):
        """
        Create an instance of the app with the testing configuration
        :return:
        """
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        """
        Create the database
        :return:
        """
        db.create_all()
        db.session.commit()

    def tearDown(self):
        """
        Drop the database tables and also remove the session
        :return:
        """
        db.session.remove()
        db.drop_all()

    @staticmethod
    def create_user() -> ci_demo.User:
        """
        Creates a user with name test and password test and stores the user in the database if the user is not yet
        present.

        :return: A user instance for the user named test.
        """

        u = ci_demo.User.query.filter(ci_demo.User.id == BaseTestCase.user_id).first()
        if u is None:
            # Create user with name test and password test
            u = ci_demo.User(id=BaseTestCase.user_id, name=BaseTestCase.user_name)
            u.update_password(BaseTestCase.user_password)
            ci_demo.db.session.add(u)
            ci_demo.db.session.commit()

        return u

    @staticmethod
    def store_user_id_in_session(client: FlaskClient, user: ci_demo.User) -> None:
        """
        Stores the id of the given user in the session to emulate a logged in user.

        :param client: The client that holds the session.
        :param user: The user to be stored in the session.
        :return: Nothing.
        """
        with client.session_transaction() as sess:
            sess['user_id'] = user.id

    @staticmethod
    def create_user_and_store_in_session(client: FlaskClient) -> ci_demo.User:
        """
        Creates a user (if necessary), and stores it in the session to emulate a logged in user.

        :param client: The client that holds the session.
        :return: The user that was created, or the instance of the user that was retrieved from the DB.
        """
        u = BaseTestCase.create_user()
        BaseTestCase.store_user_id_in_session(client, u)
        return u

    @staticmethod
    def set_workshop_step_for_user(user: ci_demo.User, step: int) -> None:
        """
        Saves a given workshop step for the given user and persists it in the database.

        :param user: The user to update the workshop step of.
        :param step: The new step for the user that needs to be persisted.
        :return: Nothing.
        """
        user.workshop_step = step
        ci_demo.db.session.commit()
