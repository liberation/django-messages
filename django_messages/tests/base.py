from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from django_messages.models import Message


# caching conditions for "performance"
auth_installed = 'django.contrib.auth' in settings.INSTALLED_APPS
relationships_installed = 'relationships' in settings.INSTALLED_APPS
notification_installed = 'notification' in settings.INSTALLED_APPS
request_context_installed = 'django.core.context_processors.request' in getattr(settings, 'TEMPLATE_CONTEXT_PROCESSORS', [])
pagination_middleware_installed = 'pagination.middleware.PaginationMiddleware' in settings.MIDDLEWARE_CLASSES
pagination_installed = 'pagination' in settings.INSTALLED_APPS

try:
    reverse('django.contrib.auth.views.login')
except:
    auth_urls_installed = False
else:
    auth_urls_installed = True

try:
    reverse('notification_notices')
except:
    notification_urls_installed = False
else:
    notification_urls_installed = True


class BaseTestCase(TestCase):
    """Makes available properties in instance TestCase to avoid running tests
       that will fail if run. This way we run only tests that are meaningful for
       the user making debugging easier
    """

    def skip_if_auth_not_installed(self):
        if not auth_installed:
            self.skipTest('Auth contrib application should be installed')

    def skip_if_auth_urls_not_installed(self):
        if not auth_urls_installed:
            self.skipTest('django.contrib.auth urls are not hooked')

    def skip_if_notification_not_installed(self):
        if not notifications_installed:
            self.skipTest('Django-notification application should be installed')

    def skip_if_relationships_not_installed(self):
        if not relationships_installed:
            self.skipTest('Django-relationships application should be installed')

    def skip_if_request_context_is_not_installed(self):
        if not request_context_installed:
            self.skipTest('Request context should be installed')

    def skip_if_pagination_middleware_is_not_installed(self):
        if not pagination_middleware_installed:
            self.skipTest('Pagination middleware should be installed')

    def skip_if_pagination_is_not_installed(self):
        if not pagination_installed:
            self.skipTest('Pagination application should be installed')

    def skip_if_notification_urls_not_installed(self):
        if not notification_urls_installed:
            self.skipTest('Notification urls are not hooked')


class DjangoMessagesTestCase(BaseTestCase):

    def send_message(self, sender, recipient, parent=None, conversation=None):
        msg = Message(
            sender=sender,
            recipient=recipient,
            subject='Subject Text',
            body='Body Text',
            parent_msg=parent,
            conversation=conversation,
        )
        msg.save()
        return msg
