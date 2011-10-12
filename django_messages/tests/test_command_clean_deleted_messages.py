import datetime
from time import time

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings

from django_messages.models import Message


class DeleteTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('user3', 'user3@example.com', '123456')
        self.user2 = User.objects.create_user('user4', 'user4@example.com', '123456')
        self.msg1 = Message(sender=self.user1, recipient=self.user2, subject='Subject Text 1', body='Body Text 1')
        self.msg2 = Message(sender=self.user1, recipient=self.user2, subject='Subject Text 2', body='Body Text 2')
        self.msg1.sender_deleted_at = datetime.datetime.now()
        self.msg2.recipient_deleted_at = datetime.datetime.now()
        self.msg1.save()
        self.msg2.save()
                
    def testBasic(self):
        self.assertEquals(Message.objects.outbox_for(self.user1).count(), 1)
        self.assertEquals(Message.objects.outbox_for(self.user1)[0].subject, 'Subject Text 2')
        self.assertEquals(Message.objects.inbox_for(self.user2).count(),1)
        self.assertEquals(Message.objects.inbox_for(self.user2)[0].subject, 'Subject Text 1')
        #undelete
        self.msg1.sender_deleted_at = None
        self.msg2.recipient_deleted_at = None
        self.msg1.save()
        self.msg2.save()
        self.assertEquals(Message.objects.outbox_for(self.user1).count(), 2)
        self.assertEquals(Message.objects.inbox_for(self.user2).count(),2)


class TestCleanDeletedMessages(TestCase):

    def call_clean_deleted_messages_command(self, dryrun=False):
        call_command('clean_deleted_messages', dryrun=dryrun)

    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'user1@example.com', '123456')
        self.user2 = User.objects.create_user('user2', 'user2@example.com', '123456')
        
    def test_dont_delete_messages(self):
        """Tests that messages that are not deleted by the user are not deleted 
        by the command"""
        Message(sender=self.user1, recipient=self.user2, subject='Subject Text 1', body='Body Text 1').save()
        self.call_clean_deleted_messages_command()
        self.assertEquals(Message.objects.all().count(), 1)
        
    def test_dont_delete_message_only_sender_deleted(self):
        """Tests that messages only deleted by the sender are not deleted by
        the command"""
        settings.DELETED_MESSAGE_MAX_AGE = 999
        # this date should match the command criteria
        sender_deleted_at = time() - settings.DELETED_MESSAGE_MAX_AGE
        sender_deleted_at = datetime.datetime.fromtimestamp(sender_deleted_at)
        # but not the message since the recipient did not delete the message
        Message(
            sender=self.user1,
            recipient=self.user2,
            subject='Subject Text 1',
            body='Body Text 1',
            sender_deleted_at=sender_deleted_at).save()
        self.call_clean_deleted_messages_command()
        self.assertEquals(Message.objects.all().count(), 1)

    def test_dont_delete_message_only_recipient_deleted(self):
        """Tests that messages only deleted by the recipient are not deleted by
        the command"""
        settings.DELETED_MESSAGE_MAX_AGE = 999
        # this date should match the command criteria
        recipient_deleted_at = time() - settings.DELETED_MESSAGE_MAX_AGE
        recipient_deleted_at = datetime.datetime.fromtimestamp(recipient_deleted_at)
        # but not the message since the sender did not delete the message
        Message(
            sender=self.user1,
            recipient=self.user2,
            subject='Subject Text 1',
            body='Body Text 1',
            recipient_deleted_at=recipient_deleted_at).save()
        self.call_clean_deleted_messages_command()
        self.assertEquals(Message.objects.all().count(), 1)
        
    def test_dont_delete_message_if_delete_not_old_enough1(self):
        """Tests that messages that are deleted by both the recipiend and the sender
        are not deleted if one of the delete action is not old enough"""
        settings.DELETED_MESSAGE_MAX_AGE = 999
        # this date should match the command criteria
        recipient_deleted_at = time() - settings.DELETED_MESSAGE_MAX_AGE
        recipient_deleted_at = datetime.datetime.fromtimestamp(recipient_deleted_at)
        sender_deleted_at = datetime.datetime.now() # doesn't match the command criteria
        # the message doesn't match command criteria
        Message(
            sender=self.user1,
            recipient=self.user2,
            subject='Subject Text 1',
            body='Body Text 1',
            recipient_deleted_at=recipient_deleted_at,
            sender_deleted_at=sender_deleted_at).save()
        self.call_clean_deleted_messages_command()
        self.assertEquals(Message.objects.all().count(), 1)

    def test_dont_delete_message_if_delete_not_old_enough2(self):
        """Tests that messages that are deleted by both the recipiend and the sender
        are not deleted if one of the delete action is not old enough"""
        settings.DELETED_MESSAGE_MAX_AGE = 999
        sender_deleted_at = time() - settings.DELETED_MESSAGE_MAX_AGE
        sender_deleted_at = datetime.datetime.fromtimestamp(sender_deleted_at)
        recipient_deleted_at = datetime.datetime.now() # doesn't match the command criteria
        Message(
            sender=self.user1,
            recipient=self.user2,
            subject='Subject Text 1',
            body='Body Text 1',
            recipient_deleted_at=recipient_deleted_at,
            sender_deleted_at=sender_deleted_at).save()
        self.call_clean_deleted_messages_command()
        self.assertEquals(Message.objects.all().count(), 1)

    def test_delete_message(self):
        """Tests that messages that are deleted by both the recipient and the sender
        are not deleted if the one of the delete action is not old enough"""
        settings.DELETED_MESSAGE_MAX_AGE = 999
        sender_deleted_at = time() - settings.DELETED_MESSAGE_MAX_AGE
        sender_deleted_at = datetime.datetime.fromtimestamp(sender_deleted_at)
        recipient_deleted_at = sender_deleted_at
        # both date match command criteria
        Message(
            sender=self.user1,
            recipient=self.user2,
            subject='Subject Text 1',
            body='Body Text 1',
            recipient_deleted_at=recipient_deleted_at,
            sender_deleted_at=sender_deleted_at).save()
        self.call_clean_deleted_messages_command()
        self.assertEquals(Message.objects.all().count(), 0)

    def test_dryrun(self):
        """Even if the Message match don't delete it because it's a dryrun"""
        settings.DELETED_MESSAGE_MAX_AGE = 999
        sender_deleted_at = time() - settings.DELETED_MESSAGE_MAX_AGE
        sender_deleted_at = datetime.datetime.fromtimestamp(sender_deleted_at)
        recipient_deleted_at = sender_deleted_at
        # both date match command criteria
        Message(
            sender=self.user1,
            recipient=self.user2,
            subject='Subject Text 1',
            body='Body Text 1',
            recipient_deleted_at=recipient_deleted_at,
            sender_deleted_at=sender_deleted_at).save()
        self.call_clean_deleted_messages_command(dryrun=True)
        self.assertEquals(Message.objects.all().count(), 1)
