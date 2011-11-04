from datetime import datetime

from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.unittest import skipIf
from django.contrib.auth.models import User

from django_messages.models import Message
from django_messages.forms import ComposeForm

from base import DjangoMessagesTestCase


class ViewBaseTestCase(DjangoMessagesTestCase):

    def setUp(self):
        self.skip_if_auth_not_installed()
        self.user1 = User.objects.create(username='user1', email='user1@example.net')
        self.user2 = User.objects.create(username='user2', email='user2@example.net')
        self.user3 = User.objects.create(username='user3', email='user3@example.net')

        self.user1.set_password('user1')
        self.user1.save()
        self.user2.set_password('user2')
        self.user2.save()
        self.user3.set_password('user3')
        self.user3.save()


class InboxViewTests(ViewBaseTestCase):

    def setUp(self):
        super(InboxViewTests, self).setUp()
        self.target_url = reverse('messages_inbox')

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_content(self):
        """Checks that the content of inbox is what we expect
        
        Messages are just those that user1 should receive and that their subject
        is available in page"""
        self.skip_if_notification_urls_not_installed()
        self.skip_if_pagination_is_not_installed()
        self.skip_if_pagination_middleware_is_not_installed()
        self.skip_if_request_context_is_not_installed()

        self.client.login(username='user1', password='user1')

        # generate messages for user1, user2, user3
        messages = []
        for i in range(10):
            message = self.send_message(self.user2, self.user1)
            message.conversation = message
            message.save()
            messages.append(message)  # gather messages

            # more messages in the database to make sure that only 
            # messages in ``messages`` are present in ``self.user1`` inbox
            message = self.send_message(self.user1, self.user2)
            message.conversation = message
            message.save()

            message = self.send_message(self.user2, self.user3)
            message.conversation = message
            message.save()

            message = self.send_message(self.user3, self.user2)
            message.conversation = message
            message.save()

        response = self.client.get(self.target_url)
        # self.user1 inbox messages
        conversations = response.context['conversations']
        conversations = sorted(conversations, key=lambda x : x.pk)
        messages = sorted(messages, key=lambda x: x.pk)
        self.assertEqual(len(conversations), len(messages))
        for index in range(len(conversations)):
            conversation = conversations[index]
            message = messages[index]
            # Check that only messages sent to self.user1 are available in template
            self.assertEqual(conversation, message)
            # Check that message subject appears in page 
            self.assertContains(response, message.subject)


class OutboxViewTests(ViewBaseTestCase):

    def setUp(self):
        super(OutboxViewTests, self).setUp()
        self.target_url = reverse('messages_outbox')

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_content(self):
        """Checks that only messages sent by ``self.user1`` are displayed"""
        self.skip_if_notification_urls_not_installed()
        self.skip_if_pagination_is_not_installed()
        self.skip_if_pagination_middleware_is_not_installed()
        self.skip_if_request_context_is_not_installed()

        self.client.login(username='user1', password='user1')

        messages = []
        for i in range(10):
            message = self.send_message(self.user1, self.user2)
            message.conversation = message
            message.save()
            messages.append(message)  # gather messages

            # more messages in the database to make sure that only 
            # messages in ``messages`` are present in ``self.user1`` outbox
            message = self.send_message(self.user2, self.user1)
            message.conversation = message
            message.save()

            message = self.send_message(self.user2, self.user3)
            message.conversation = message
            message.save()

            message = self.send_message(self.user3, self.user2)
            message.conversation = message
            message.save()

        response = self.client.get(self.target_url)
        conversations = response.context['conversations']
        conversations = sorted(conversations, key=lambda x : x.pk)
        messages = sorted(messages, key=lambda x: x.pk)
        self.assertEqual(len(conversations), len(messages))
        for index in range(len(conversations)):
            conversation = conversations[index]
            message = messages[index]
            # Check that only messages sent to self.user1 are available in template
            self.assertEqual(conversation, message)
            # Check that message subject appears in page 
            self.assertContains(response, message.subject)


class TrashViewTests(ViewBaseTestCase):

    def setUp(self):
        super(TrashViewTests, self).setUp()
        self.target_url = reverse('messages_trash')

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_content(self):
        """Test that only messages from user1 that were deleted are present in trash"""
        self.skip_if_notification_urls_not_installed()
        self.skip_if_pagination_is_not_installed()
        self.skip_if_pagination_middleware_is_not_installed()
        self.skip_if_request_context_is_not_installed()

        self.client.login(username='user1', password='user1')

        messages = []
        for i in range(10):
            message = self.send_message(self.user1, self.user2)
            message.conversation = message
            message.sender_deleted_at = datetime.now()
            message.save()
            messages.append(message)  # gather messages
            message = self.send_message(self.user2, self.user1)
            message.conversation = message
            message.recipient_deleted_at = datetime.now()
            message.save()
            messages.append(message)  # gather messages

            message = self.send_message(self.user1, self.user2)
            message.conversation = message
            message.save()
            message = self.send_message(self.user2, self.user1)
            message.conversation = message
            message.save()

            # more messages in the database to make sure that only 
            # messages in ``messages`` are present in ``self.user1`` outbox
            message = self.send_message(self.user2, self.user3)
            message.conversation = message
            message.recipient_deleted_at = datetime.now()
            message.sender_deleted_at = datetime.now()
            message.save()

            message = self.send_message(self.user3, self.user2)
            message.conversation = message
            message.recipient_deleted_at = datetime.now()
            message.sender_deleted_at = datetime.now()
            message.save()

        response = self.client.get(self.target_url)
        conversations = response.context['conversations']
        conversations = sorted(conversations, key=lambda x : x.pk)
        messages = sorted(messages, key=lambda x: x.pk)
        self.assertEqual(len(conversations), len(messages))
        for index in range(len(conversations)):
            conversation = conversations[index]
            message = messages[index]
            # Check that only messages sent to self.user1 are available in template
            self.assertEqual(conversation, message)
            # Check that message subject appears in page 
            self.assertContains(response, message.subject)


class ComposeViewTests(ViewBaseTestCase):

    def setUp(self):
        super(ComposeViewTests, self).setUp()
        
        #check dependencies
        self.skip_if_pagination_is_not_installed()
        self.skip_if_pagination_middleware_is_not_installed()
        
        self.target_url = reverse('messages_compose')

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_get_with_proper_form(self):
        """Integration test, this test rely on the fact that the form used in this
        view is tested in ``test.test_forms``. This test can fail for several reason:
            - Django fails to reverse the url: You may not have included the
              ``messages_compose`` url in the url routing system of your project
            - Wrong status code: the url named ``messages_compose`` exists but does
              not return a 200 status code. 
            - 
        """
        self.client.login(username='user1', password='user1')
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.context['form'], ComposeForm))

    def test_submit(self):
        self.client.login(username='user1', password='user1')
        subject = 'random subject for testing'
        body = 'body body body body body body'
        response = self.client.post(self.target_url, 
            {
                'recipient': 'user2',
                'subject': subject,
                'body': body,
            }
        )

        query = Message.objects.inbox_for(self.user2)
        count = query.count()
        self.assertIsNot(0, count)
        message = query[0]
        self.assertEqual(subject, message.subject)
        self.assertEqual(body, message.body)
        self.assertEqual(self.user1, message.sender)
        redirect_url = reverse('messages_detail',
            kwargs={
                'conversation_id' : message.conversation_id
            }
        )
        self.assertRedirects(response, redirect_url)
    
    def test_submit_redirect_next(self):
        """Tests that after submit the user is redirected to next parameter provided
        in query string"""
        self.client.login(username='user1', password='user1')
        subject = 'random subject for testing'
        body = 'body body body body body body'
        redirect_url = '/inbox/'  # random url that doesn't redirect or 404
        target_url = self.target_url + '?next=' + redirect_url
        response = self.client.post(target_url, 
            {
                'recipient': 'user2',
                'subject': subject,
                'body': body,
            }
        )
        
        self.assertRedirects(response, redirect_url)

    def test_get_with_recipient(self):
        """Checks that if the ``username`` argument is provided in the url, the 
        form is filled with that username"""
        self.client.login(username='user1', password='user1')
        subject = 'random subject for testing'
        body = 'body body body body body body'
        target_url = reverse('messages_compose_to', kwargs={'recipient': 'user2'})
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user2', response.content)

    def test_get_with_invalid_recipient(self):
        """Checks that if the ``username`` provided is invalid the user is redirect
        to vanilla form"""
        self.client.login(username='user1', password='user1')
        subject = 'random subject for testing'
        body = 'body body body body body body'
        target_url = reverse('messages_compose_to', kwargs={'recipient': 'jackson'})
        response = self.client.get(target_url)
        redirect_url = reverse('messages_compose')
        self.assertRedirects(response, redirect_url)


class ReplyViewTests(ViewBaseTestCase):

    def setUp(self):
        super(ReplyViewTests, self).setUp()
        self.message = self.send_message(self.user1, self.user2)
        self.message.conversation = self.message
        self.message.save()
        self.target_url = reverse('messages_reply', args=(self.message.pk,))

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_get_with_proper_form(self):
        """Integration test, form tests are done in ``test_forms``"""
        self.client.login(username='user1', password='user1')
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.context['form'], ComposeForm))

    def test_submit(self):
        self.client.login(username='user1', password='user1')
        subject = 'random subject for testing'
        body = 'body body body body body body'
        response = self.client.post(self.target_url, 
            {
                'subject': subject,
                'body': body,
            }
        )
        redirect_url = reverse('messages_detail', kwargs={'conversation_id' : self.message.conversation_id})
        self.assertRedirects(response, redirect_url)

    def test_get_with_invalid_user(self):
        """If an user not involved in the conversation should display a 404"""
        self.client.login(username='user3', password='user3')
        response = self.client.get(self.target_url)
        self.assertEqual(404, response.status_code)

    def test_post_with_invalid_user(self):
        """If an user not involved in the conversation should display a 404
        and not store the message"""
        self.client.login(username='user3', password='user3')
        subject = 'random subject for testing'
        body = 'body body body body body body'
        response = self.client.post(self.target_url, 
            {
                'subject': subject,
                'body': body,
            }
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(1, Message.objects.count())


class DeleteViewTests(ViewBaseTestCase):

    def setUp(self):
        super(DeleteViewTests, self).setUp()
        
        #check dependencies
        self.skip_if_pagination_middleware_is_not_installed()
        self.skip_if_pagination_is_not_installed()
        
        self.message = self.send_message(self.user1, self.user2)
        self.message.conversation = self.message
        self.message.save()
        self.target_url = reverse('messages_delete')

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_get_is_a_404(self):
        self.client.login(username='user1', password='user1')
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 404)

    def test_submit(self):
        self.client.login(username='user1', password='user1')
        ids = [self.message.pk] + [10, 11, 12]  # invalid ids are accepted
        response = self.client.post(self.target_url, {'ids': ids})
        self.assertRedirects(response, reverse('messages_inbox'))
        # fetch the message from db to update the values
        self.message = Message.objects.get(id=self.message.id)
        # test that the sender (user1) deleted the message
        self.assertIsNotNone(self.message.sender_deleted_at)

    def test_submit_redirect_next(self):
        """Checks that after submition the user is redirect to next provided query
        string parameter"""
        self.client.login(username='user1', password='user1')
        ids = [1,2,3,4,5,6,7,8,9]
        next = reverse('messages_outbox')
        target_url = '%s?next=%s' % (self.target_url, next)
        response = self.client.post(target_url, {'ids': ids})
        self.assertRedirects(response, next)


class UndeleteViewTests(ViewBaseTestCase):

    def setUp(self):
        super(UndeleteViewTests, self).setUp()
        #check dependencies
        self.skip_if_pagination_middleware_is_not_installed()
        self.skip_if_pagination_is_not_installed()
        
        self.message = self.send_message(self.user1, self.user2)
        self.message.conversation = self.message
        self.message.sender_deleted_at = datetime.now()
        self.message.save()
        self.target_url = reverse('messages_undelete')

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

    def test_get_is_a_404(self):
        self.client.login(username='user1', password='user1')
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 404)

    def test_submit(self):
        self.client.login(username='user1', password='user1')
        ids = [self.message.pk]
        response = self.client.post(self.target_url, {'ids': ids})
        self.assertRedirects(response, reverse('messages_inbox'))
        # fetch the message from db to update the values
        self.message = Message.objects.get(id=self.message.id)
        # test that the sender (user1) deleted the message
        self.assertIsNone(self.message.sender_deleted_at)

    def test_submit_redirect_next(self):
        """Checks that user is redirected after submition to next query string parameter"""

        self.client.login(username='user1', password='user1')
        ids = [self.message.pk]
        next = reverse('messages_outbox')
        target_url = '%s?next=%s' % (self.target_url, next)
        response = self.client.post(target_url, {'ids': ids})
        self.assertRedirects(response, next)


def ViewTests(ViewBaseTestCase):
    """Conversation detail view tests, url endpoint is ``messages_detail``"""
    def setUp(self):
        """Create a conversation with one message and set ``self.target_url``"""
        super(ViewTests, self).setUp()
        message = self.send_message(self.user1, self.user2)
        message.conversation = message
        message.save()
        self.target_url = reverse('messages_detail', args=(self.message.pk,))

    def test_get_by_sender(self):
        """The user that started a conversation can display the conversation"""
        self.client.login(username='user1', password='user1')
        response = self.client.get(self.target_url)
        self.assertEqual(200, response.status_code)

    def test_get_by_recipient(self):
        """The user that is the recipient of the message can display the conversation"""
        self.client.login(username='user2', password='user2')
        response = self.client.get(self.target_url)
        self.assertEqual(200, response.status_code)
    
    def test_get_by_someone_else(self):
        """Someone not involved in the conversation cannot display the conversation"""
        self.client.login(username='user3', password='user3')
        response = self.client.get(self.target_url)
        self.assertEqual(404, response.status_code)

    def test_login_required(self):
        response = self.client.get(self.target_url)
        login_url = reverse('django.contrib.auth.views.login')
        redirect_url = 'http://testserver%s?next=%s' % (login_url, self.target_url)
        self.assertRedirects(response, redirect_url)

