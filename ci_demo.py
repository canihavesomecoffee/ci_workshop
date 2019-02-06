import os
import random
import flask
import typing

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from functools import wraps
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length
from xhtml2pdf import pisa

from hint import Hint, WorkshopHints

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', '')
app.config['SECRET_KEY'] = 'foo-bar'
app.config['CSRF_SESSION_KEY'] = 'foo-bar'
db = SQLAlchemy(app)

workshop_hints = WorkshopHints()


class User(db.Model):
    """
    Represents a user in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(255), nullable=False)
    workshop_step = db.Column(db.Integer, default=1, nullable=False)
    hints = relationship("UserHints", back_populates="user")

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


class UserHints(db.Model):
    """
    Keep track of taken hints by a user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User", back_populates="hints")


class LoginForm(FlaskForm):
    """
    Represents the login form.
    """
    name = StringField('Name', [DataRequired(), Length(max=10)])
    password = PasswordField('Password', [DataRequired()])
    submit = SubmitField('Log in')


class ContactForm(FlaskForm):
    """
    Represents the contact form.
    """
    name = StringField('Name', [DataRequired()])
    email = EmailField('Email address', [DataRequired()])
    message = TextAreaField('Your message', [DataRequired()])
    submit = SubmitField('Send')


class WorkshopForm(FlaskForm):
    """
    Holds the buttons to navigate through the workshop.
    """
    next = SubmitField('Proceed to next step')
    previous = SubmitField('Return one step')


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
    'workshop_overview.html',
    'workshop_final.html'
]


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


def get_valid_step(current_step: int, max_step: int) -> int:
    """
    Checks if the current step is within boundaries and returns a corrected step.

    :param current_step: The current step to check.
    :param max_step: The maximum allowed step.
    :return: A corrected step between 1 and the maximum step.
    """
    if current_step < 1:
        current_step = 1
    elif current_step > max_step:
        current_step = max_step
    return current_step


def get_active_hints(user: User, hints: WorkshopHints) -> typing.List[Hint]:
    """
    Retrieves the hints that were already activated for this user and workshop step.

    :param user: The current user.
    :param hints: All available hints.
    :return: A list of hints.
    """
    visible_hints = [hint.id for hint in user.hints]
    return list(filter(lambda h: h.id in visible_hints, hints.get_hints_for_step(user.workshop_step)))


def retrieve_next_hint(user: User, current_step: int, hints: WorkshopHints) -> typing.Optional[Hint]:
    """
    Retrieves the next hint (if available) for the user and the current step.

    :param user: The current user.
    :param current_step: The current step for the user
    :param hints: All available hints.
    :return: A hint, or None when not found.
    """
    used_hints = [hint.id for hint in user.hints]

    def filter_criterium(hint):
        return hint.id not in used_hints

    hints_for_step = list(filter(filter_criterium, hints.get_hints_for_step(current_step)))
    hints_for_step.sort(key=lambda h: h.id)
    return None if len(hints_for_step) == 0 else hints_for_step[0]


def unlock_all_hints_for_step(current_step: int, user: User, hints: WorkshopHints) -> None:
    """
    Unlocks all hints for a user on a certain step.

    :param current_step: The current step for the user
    :param user: The current user.
    :param hints: All available hints.
    :return: void.
    """
    active_hints_current_step = [h.id for h in get_active_hints(user, hints)]
    for hint in hints.get_hints_for_step(current_step):
        if hint.id not in active_hints_current_step:
            user_hint = UserHints(id=hint.id, user_id=user.id)
            db.session.add(user_hint)
    db.session.commit()


def get_rendered_block_content(template: str, block: str = "content", **kwargs) -> str:
    """
    Retrieves a given block from a given template, and renders it into html.

    :param template: The template to retrieve the block from.
    :param block: The block of content to retrieve and render.
    :param kwargs: Optional arguments to be passed for rendering the block.
    :return: The rendered block.
    """
    goal_template = app.jinja_env.get_template(template)
    goal_block = goal_template.blocks[block]
    goal_context = goal_template.new_context(kwargs)
    return ''.join(goal_block(goal_context))


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
    current_step = flask.g.user.workshop_step
    max_step = len(workshop_steps)

    form = WorkshopForm()
    if form.validate_on_submit():
        # Store new step
        if form.next.data:
            unlock_all_hints_for_step(current_step, flask.g.user, workshop_hints)
            current_step += 1
        else:
            current_step -= 1

        current_step = get_valid_step(current_step, max_step)

        flask.g.user.workshop_step = current_step
        db.session.commit()

    return flask.render_template(
        workshop_steps[current_step - 1], form=form, current_step=current_step, max_step=max_step,
        hints=get_active_hints(flask.g.user, workshop_hints),
        maxHintsForStep=len(workshop_hints.get_hints_for_step(current_step))
    )


@app.route('/my_workshop/hint', methods=['POST'])
@login_required
def get_hint() -> flask.Response:
    current_step = get_valid_step(flask.g.user.workshop_step, len(workshop_steps))
    hint = retrieve_next_hint(flask.g.user, current_step, workshop_hints)
    if hint is not None:
        sorted_hints = sorted(workshop_hints.get_hints_for_step(current_step), key=lambda h: h.id)
        nr = sorted_hints.index(hint) + 1
        user_hint = UserHints(id=hint.id, user_id=flask.g.user.id)
        db.session.add(user_hint)
        db.session.commit()
        return flask.jsonify(
            content=flask.render_template("hint.html", hint=hint, nr=nr),
            top=flask.render_template("hint_top.html", hint=hint, nr=nr),
            last=(len(sorted_hints) == nr)
        )
    return flask.jsonify(error="No hints available")


@app.route('/about')
def about() -> flask.Response:
    """
    Shows an about page that lists all used libraries.

    :return:
    """
    return flask.render_template('about.html')


@app.route('/download_pdf')
def download_pdf() -> flask.Response:
    """
    Triggers the download of a single page PDF of the worskhop.

    :return:
    """
    pdf_name = "workshop.pdf"
    if not os.path.isfile(pdf_name):
        rendered_template = flask.render_template(
            "single_page_pdf.html",
            goal_block=get_rendered_block_content("workshop.html", ignore=True),
            about_block=get_rendered_block_content("about.html"),
            steps=[get_rendered_block_content(
                step,
                block="step_content",
                current_step=(workshop_steps.index(step) + 1),
                ignore=True
            ) for step in workshop_steps],
            hints=workshop_hints.get_all_hints()
        )
        with open(pdf_name, "w+b") as fh:
            status = pisa.CreatePDF(rendered_template, dest=fh)
            if status.err:
                flask.abort(400)

    return flask.send_file(pdf_name, as_attachment=True, cache_timeout=-1)


@app.route('/contact')
def contact() -> flask.Response:
    """
    Shows a contact form for users

    :return:
    """
    form = ContactForm()
    return flask.render_template('contact.html', form=form)


if __name__ == '__main__':
    app.run()
