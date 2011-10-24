from django.test import TestCase

from base import *


class DependenciesTestCase(BaseTestCase):

    def test_auth_app(self):
        """Some tests needs self.auth to be installed to be able to run correctly"""
        self.assertTrue(auth_installed)

    def test_relationships_app(self):
        """Tests specific to django-relationship will not be run if it is not installed"""
        self.assertTrue(relationships_installed)

    def test_notifications_app(self):
        """Tests specific to django-notification will not be run if it is not installed"""
        self.assertTrue(notification_installed)

    def test_login_view_hooked(self):
        """Login view should be hooked in ``urls.py`` to be able to tests
        ``login_required`` redirect with ``self.assertRedirects``"""
        self.assertTrue(auth_urls_installed)

    def test_request_context_installed(self):
        self.assertTrue(request_context_installed)

    def test_pagination_middleware_installed(self):
        self.assertTrue(pagination_middleware_installed)

    def test_pagination_installed(self):
        self.assertTrue(pagination_installed)

    def test_notifications_urls_installed(self):
        self.assertTrue(notification_urls_installed)
