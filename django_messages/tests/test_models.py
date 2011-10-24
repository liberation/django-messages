from datetime import datetime

from django.core import mail
from django.contrib.auth.models import User
from django_messages.models import Message, inbox_count_for

from base import DjangoMessagesTestCase


class MessageTests(DjangoMessagesTestCase):

    def setUp(self):
        self.skip_if_auth_not_installed()
        self.skip_if_notification_not_installed()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='123456')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='123456')
        self.user3 = User.objects.create_user(username='user3', email='user3@example.com', password='123456')

    def test_user_sent_messages(self):
        """Tests that a message sent by a user is available in ``sent_messages``
        property of the ``User`` model and only to the user who sent the message"""
        mail.outbox = []
        msg = self.send_message(self.user1, self.user2)

        self.assertEquals(self.user1.sent_messages.all().count(), 1)
        self.assertEquals(self.user2.sent_messages.all().count(), 0)

        self.assertEquals(self.user3.sent_messages.all().count(), 0)

        self.assertEquals(len(mail.outbox), 1)
        mail.outbox = []

    def test_user_received_messages(self):
        """Tests that a message sent to a user is available in ``received_messages``
        property of the ``User`` model and only to the user the message was sent"""
        msg = self.send_message(self.user1, self.user2)

        self.assertEquals(self.user1.received_messages.all().count(), 0)
        self.assertEquals(self.user2.received_messages.all().count(), 1)
        self.assertEquals(self.user3.received_messages.all().count(), 0)

    def test_message_next_messages(self):
        """Tests that a message sent as children of a message is accessible as an
        item of the ``next_messages`` property of the parent message"""

        parent = self.send_message(self.user1, self.user2)

        self.assertEquals(parent.next_messages.all().count(), 0)

        msg = self.send_message(self.user1, self.user2, parent=parent)

        self.assertEquals(parent.next_messages.all().count(), 1)
        self.assertEquals(parent.next_messages.all()[0].pk, msg.pk)

    def test_message_is_new(self):
        """If the message is not read is new"""
        msg = self.send_message(self.user1, self.user2)

        self.assertTrue(msg.new())

    def test_message_is_not_new(self):
        """If the message ``read_at`` property is set to something, the message
        is considered read"""
        msg = self.send_message(self.user1, self.user2)
        msg.read_at = datetime.now()

        self.assertFalse(msg.new())

    def test_message_is_replied(self):
        """If the message is ``replied_at`` property is set to something, the message
        is considered read"""
        msg = self.send_message(self.user1, self.user2)
        msg.replied_at = datetime.now()
        self.assertTrue(msg.replied())

    def test_message_sent_is_set(self):
        """Once a message is sent, ``sent_at`` property should be set"""
        msg = self.send_message(self.user1, self.user2)
        self.assertIsNotNone(msg.sent_at)

    def test_user_inbox_is_initialy_empty(self):
        self.assertEquals(inbox_count_for(self.user1), 0)

    def test_user_inbox(self):
        """Tests that only the user a message was sent has an inbox count non null"""
        msg = self.send_message(self.user1, self.user2)

        self.assertEquals(inbox_count_for(self.user1), 0)  # sender
        self.assertEquals(inbox_count_for(self.user2), 1)  # recipient
        self.assertEquals(inbox_count_for(self.user3), 0)  # random user

    def test_user_inbox_only_unread_message(self):
        msg = self.send_message(self.user1, self.user2)
        msg.read_at = datetime.now()  # set message read
        msg.save()

        self.assertEquals(inbox_count_for(self.user2), 0)

    def test_user_inbox_not_deleted_messages(self):
        msg = self.send_message(self.user1, self.user2)
        msg.recipient_deleted_at = datetime.now()  # recipient deleted conversation thus the message
        msg.save()

        self.assertEquals(inbox_count_for(self.user2), 0)
