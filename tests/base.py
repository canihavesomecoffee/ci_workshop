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
            u = ci_demo.User(id=1, name='test', password='')
            ci_demo.db.session.add(u)
            ci_demo.db.session.commit()

        return u

    @staticmethod
    def store_user_id_in_session(client: FlaskClient, user: ci_demo.User):
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
