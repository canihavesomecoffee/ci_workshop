import requests
from flask_testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from ci_demo import app, db


class BaseSelenium(LiveServerTestCase):
    def create_app(self):
        """
        Create an instance of the app with the testing configuration
        """
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.sql'
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        # Default port is 5000
        app.config['LIVESERVER_PORT'] = 8888
        # Default timeout is 5 seconds
        app.config['LIVESERVER_TIMEOUT'] = 10
        return app

    def setUp(self):
        """
        Create the database
        :return:
        """
        db.create_all()
        db.session.commit()
        firefox_options = Options()
        firefox_options.add_argument("-headless")
        self.browser = webdriver.Firefox(firefox_options=firefox_options)
        self.browser.implicitly_wait(10)

    def tearDown(self):
        """
        Drop the database tables and also remove the session
        :return:
        """
        db.session.remove()
        db.drop_all()

    def test_server_is_up_and_running(self):
        response = requests.get(self.get_server_url())
        self.assertEqual(response.status_code, 200)


class TestNavBar(BaseSelenium):
    def test_navbar_contains_exactly_4_links(self):
        # Given
        expected_items_in_navbar = 4
        self.browser.get(self.get_server_url())
        nav_bar = self.browser.find_element_by_id("navbarCollapse")
        # When
        items_in_nav_bar = nav_bar.find_elements_by_class_name("nav-item")
        # Then
        self.assertEqual(expected_items_in_navbar, len(items_in_nav_bar))


class TestContactForm(BaseSelenium):
    def test_contact_form_is_shown_when_button_is_clicked(self):
        # Given
        number_of_wanted_contact_forms = 1
        self.browser.get(self.get_server_url())
        nav_bar = self.browser.find_element_by_id("navbarCollapse")
        contact_button = nav_bar.find_element_by_link_text("Contact")
        # When
        contact_button.click()
        contact_forms = self.browser.find_elements_by_id("contact-form")
        # Then
        self.assertEqual(number_of_wanted_contact_forms, len(contact_forms))
