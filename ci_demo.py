import os
import random
import flask
import typing
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from functools import wraps
from passlib.apps import custom_app_context as pwd_context
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', '')
app.config['SECRET_KEY'] = 'foo-bar'
app.config['CSRF_SESSION_KEY'] = 'foo-bar'
db = SQLAlchemy(app)

dashboard_images = [
    'img/welcomeA.jpg',
    'img/welcomeB.jpg',
    'img/welcomeC.jpg'
]

workshop_steps = [
    'workshop_github.html',
    'workshop_codecov.html',
    'workshop_heroku.html',
    'workshop_travis.html',
    'workshop_overview.html'
]


class User(db.Model):
    """
    Represents a user in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(255), nullable=False)
    workshop_step = db.Column(db.Integer, default=1, nullable=False)

    def is_password_valid(self, password: str) -> bool:
        """
        Checks if the entered password matches the stored hash.

        :param password: The password to be validated.
        :return : Validity of password.
        """
        return pwd_context.verify(password, self.password)

    def update_password(self, new_password: str) -> None:
        """
        Updates the password to a new one.

        :param new_password: The new password to be updated
        """
        self.password = pwd_context.encrypt(new_password, category='admin')


class LoginForm(FlaskForm):
    """
    Represents the login form.
    """
    name = StringField('Name', [DataRequired(), Length(max=10)])
    password = PasswordField('Password', [DataRequired()])
    submit = SubmitField('Log in')


class WorkshopForm(FlaskForm):
    """
    Holds the buttons to navigate through the workshop.
    """
    next = SubmitField('Proceed to next step')
    previous = SubmitField('Return one step')


def login_required(wrapped_method: typing.Callable) -> typing.Callable:
    """
    Decorator that redirects to the login page if a user is not logged in.

    :param wrapped_method: The method to wrap.
    :return:
    """
    @wraps(wrapped_method)
    def decorated_function(*args, **kwargs):
        if flask.g.user is None:
            return flask.redirect(flask.url_for('login', next=flask.request.endpoint))

        return wrapped_method(*args, **kwargs)

    return decorated_function


@app.before_request
def before_request() -> None:
    user_id = flask.session.get('user_id', 0)
    flask.g.user = User.query.filter(User.id == user_id).first()


@app.route('/')
def dashboard() -> flask.Response:
    """
    Shows the 'dashboard', or the 'index' of this application.

    :return:
    """
    return flask.render_template('dashboard.html', image=dashboard_images[random.randint(0, len(dashboard_images) - 1)])


@app.route('/login', methods=['GET', 'POST'])
def login() -> flask.Response:
    """
    Shows a login page, and optionally processes the login attempt.

    :return:
    """
    form = LoginForm()
    redirect_location = flask.request.args.get('next', '')
    if form.validate_on_submit():
        # Check if user exists
        user = User.query.filter(User.name == form.name.data).first()

        if user is None:
            user = User(name=form.name.data)
            user.update_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            logged_in = True
        else:
            logged_in = user.is_password_valid(form.password.data)

        if logged_in:
            flask.session['user_id'] = user.id

            if len(redirect_location) == 0:
                return flask.redirect("/")

            return flask.redirect(flask.url_for(redirect_location))

        else:
            flask.flash('Wrong username or password', 'error-message')

    return flask.render_template('login.html', form=form, next=redirect_location)


@app.route('/workshop')
def workshop() -> flask.Response:
    """
    Shows the page that has the goal of the workshop.

    :return:
    """
    return flask.render_template('workshop.html')


@app.route('/my_workshop', methods=['GET', 'POST'])
@login_required
def my_workshop() -> flask.Response:
    """
    Keeps track of the progress of the user throughout steps.

    :return:
    """
    step = flask.g.user.workshop_step
    max_step = len(workshop_steps)

    form = WorkshopForm()
    if form.validate_on_submit():
        # Store new step
        if form.next.data:
            step = step + 1
        else:
            step = step - 1

        if step < 1:
            step = 1
        elif step > max_step:
            step = max_step

        flask.g.user.workshop_step = step
        db.session.commit()

    return flask.render_template(workshop_steps[step - 1], form=form, current_step=step, max_step=max_step)


@app.route('/about')
def about() -> flask.Response:
    """
    Shows an about page that lists all used libraries.

    :return:
    """
    return flask.render_template('about.html')


if __name__ == '__main__':
    app.run()
