from flask.testing import FlaskClient

import ci_demo
from ci_demo import app, db
from flask_testing import TestCase


class BaseTestCase(TestCase):
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
        u = ci_demo.User.query.filter(ci_demo.User.id == 1).first()
        if u is None:
            # Create user with name test and password test
            u = ci_demo.User(id=1, name='test', password='$6$rounds=1024000$XSPSVlwAI0m2l86t$aJoqULIwRFlIL7oWY6z.R1blz4yfe9pYSdsVMgm7XZK4NiJC2xEluAlS/JEWEsRBMut4X3AgSk9VWHpl4pekH.')
            ci_demo.db.session.add(u)
            ci_demo.db.session.commit()

        return u

    @staticmethod
    def store_user_id_in_session(client: FlaskClient, user: ci_demo.User):
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
