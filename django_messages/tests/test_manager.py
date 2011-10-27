from datetime import datetime, timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django_messages.models import Message
from django.db import connection
from django.conf import settings

from base import DjangoMessagesTestCase


class ManagerTests(DjangoMessagesTestCase):

    def setUp(self):
        self.skip_if_auth_not_installed()
        self.user1 = User.objects.create_user('user1', 'user1@example.com', '123456')
        self.user2 = User.objects.create_user('user2', 'user2@example.com', '123456')
        self.user3 = User.objects.create_user('user3', 'user3@example.com', '123456')

    def test_related(self):
        """if you query database thanks to the related property, the recipient 
        and sender shouldn't trigger new queries"""
        self.send_message(self.user1, self.user2)
        settings.DEBUG = True  # so that django populates connection.queries
        msg = Message.objects.related[0]

        sender = msg.sender
        recipient = msg.recipient

        self.assertEquals(len(connection.queries), 1)
        settings.DEBUG = False

    def test__conversation(self):
        """Tests that _conversation property returns ids of the latest message for
        each conversation in order of conversation"""
        
        conversation = self.send_message(self.user1, self.user2)
        conversation.conversation = conversation
        conversation.save()
        
        _conversations = Message.objects._conversations
        
        self.assertEquals(_conversations.count(), 1)
        self.assertEquals(_conversations[0], conversation.pk)
        
    def test_inbox_for_user_is_empty(self):
        self.assertEquals(Message.objects.inbox_for(self.user1).count(), 0)
        
    def test_inbox_for_user_is_not_empty(self):
        """Tests that recipient inbox is not empty, but inbox of other user is"""
        self.send_message(self.user1, self.user2)
        self.assertEquals(Message.objects.inbox_for(self.user1).count(), 0)
        self.assertEquals(Message.objects.inbox_for(self.user2).count(), 1)
        self.assertEquals(Message.objects.inbox_for(self.user3).count(), 0)
        
    def test_inbox_for_user_without_deleted_messages(self):
        """Tests that deleted messages aren't display in inbox"""
        msg = self.send_message(self.user1, self.user2)
        msg.recipient_deleted_at = datetime.now()
        msg.save()
        self.assertEquals(Message.objects.inbox_for(self.user2).count(), 0)
        
    def test_outbox_for_user_is_empty(self):
        self.assertEquals(Message.objects.outbox_for(self.user1).count(), 0)
        
    def test_outbox_for_user_is_not_empty(self):
        """Tests that only the sender has objects in its outbox"""
        self.send_message(self.user1, self.user2)
        self.assertEquals(Message.objects.outbox_for(self.user1).count(), 1)
        self.assertEquals(Message.objects.outbox_for(self.user2).count(), 0)
        self.assertEquals(Message.objects.outbox_for(self.user3).count(), 0)
        
    def test_trash_for_user_is_empty(self):
        self.assertEquals(Message.objects.trash_for(self.user1).count(), 0)

    def test_trash_not_empty_user_as_recipient(self):
        """Tests that a deleted item is only available to the user that deleted it"""
        msg = self.send_message(self.user1, self.user2)
        msg.recipient_deleted_at = datetime.now()
        msg.save()
        settings.HIDE_DELETED_MESSAGES_AFTER = 999
        self.assertEquals(Message.objects.trash_for(self.user2).count(), 1)
        self.assertEquals(Message.objects.trash_for(self.user1).count(), 0)
        self.assertEquals(Message.objects.trash_for(self.user3).count(), 0)
        
    def test_trash_not_empty_user_as_sender(self):
        """Tests that a deleted item is only available to the user that deleted it"""
        msg = self.send_message(self.user1, self.user2)
        msg.sender_deleted_at = datetime.now()
        msg.save()
        settings.HIDE_DELETED_MESSAGES_AFTER = 999
        self.assertEquals(Message.objects.trash_for(self.user2).count(), 0)
        self.assertEquals(Message.objects.trash_for(self.user1).count(), 1)
        self.assertEquals(Message.objects.trash_for(self.user3).count(), 0)

    def test_trash_do_not_show_old_messages(self):
        """Tests that a deleted item is only available to the user that deleted it"""
        msg = self.send_message(self.user1, self.user2)
        settings.HIDE_DELETED_MESSAGES_AFTER = 999
        old_enough = datetime.now() - timedelta(days=1000)
        
        # both user deleted the message
        msg.recipient_deleted_at = old_enough
        msg.sender_deleted_at = old_enough
        msg.save()
        
        # both user should have an empty trash
        self.assertEquals(Message.objects.trash_for(self.user2).count(), 0)
        self.assertEquals(Message.objects.trash_for(self.user1).count(), 0)

    def test_get_conversation_one_message(self):
        conversation = self.send_message(self.user1, self.user2)
        conversation.conversation = conversation
        conversation.save()
        
        count = Message.objects.get_conversation(conversation).count()
        self.assertEquals(count, 1)
        
    def test_get_conversation(self):
        conversation = self.send_message(self.user1, self.user2)
        conversation.conversation = conversation
        conversation.save()
        
        for i in range(5):
            self.send_message(self.user1, self.user2, conversation=conversation)

        conversation = Message.objects.get_conversation(conversation)
        count = conversation.count()
        self.assertEquals(count, 6)
        
        # Messages should be ordered by sent_at
        sent_at = conversation[0].sent_at
        
        for message in conversation[1:]:
            self.assertTrue(message.sent_at >= sent_at)
            sent_at = message.sent_at

    def test_get_conversations_with_one_message(self):
        conversation1 = self.send_message(self.user1, self.user2)
        conversation1.conversation = conversation1
        conversation1.save()
        conversation2 = self.send_message(self.user1, self.user2)
        conversation2.conversation = conversation2
        conversation2.save()
                
        messages = Message.objects.get_conversations((conversation1, conversation2))
        self.assertEquals(messages.count(), 2)
        self.assertTrue(messages[1].sent_at>messages[0].sent_at)
        
    def test_get_conversations_with_several_message(self):
        conversation1 = self.send_message(self.user1, self.user2)
        conversation1.conversation = conversation1
        conversation1.save()
        conversation2 = self.send_message(self.user1, self.user2)
        conversation2.conversation = conversation2
        conversation2.save()
        
        for i in range(5):
            self.send_message(self.user1, self.user2, conversation=conversation1)
            self.send_message(self.user1, self.user2, conversation=conversation2)

        conversations = Message.objects.get_conversations((conversation1, conversation2))
        count = conversations.count()
        self.assertEquals(count, 12)

