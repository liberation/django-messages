from django.test import TestCase

from django_messages.models import Message


class DjangoMessagesTestCase(TestCase):
   
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
