from django.contrib.auth.models import User

from django_messages.forms import ComposeForm
# django-relationships should, be installed if you want to run the tests
from relationships.models import RelationshipStatus, Relationship

from base import BaseTestCase


class ComposeFormTests(BaseTestCase):

    def setUp(self):
        self.skip_if_auth_not_installed()
        self.skip_if_relationships_not_installed()
        self.user1 = User.objects.create(username="user 1")
        self.user2 = User.objects.create(username="user 2")

    def test_clean_subject(self):
        form = ComposeForm(
            {
                'recipient': self.user2.username,
                'subject': 'X'*123,
                'body': 'this is not empty',
            }, 
            sender=self.user1,
        )
        
        self.assertTrue(form.is_valid())
        subject = form.cleaned_data['subject']
        
        self.assertEquals(120, len(subject))

    def test_valid_sender_recipient_transaction(self):
        """If the recipient blacklisted the sender, the form should not
        validate and report an error"""
        blocking = RelationshipStatus.objects.get(from_slug='blocking')
        relationship = Relationship(
            from_user=self.user2,
            to_user=self.user1,
            status=blocking
        )
        relationship.save()
        form = ComposeForm(
            {
                'recipient': self.user2.username,
                'subject': 'this is not empty',
                'body': 'this is not empty',
            }, 
            sender=self.user1,
        )
        self.assertFalse(form.is_valid())
        errors = form.errors['recipient']
        self.assertEquals(1, len(errors))
        expected_error_message = u"%(recipient)s has blacklisted you, you can't message him any more."
        expected_error_message = expected_error_message % {'recipient': self.user2}
        self.assertEquals(expected_error_message, errors[0])

    def test_save(self):
        form = ComposeForm(
            {
                'recipient': self.user2.username,
                'subject': 'this is not empty',
                'body': 'this is not empty',
            }, 
            sender=self.user1,
        )
        self.assertTrue(form.is_valid())
        massage = form.save()
        self.assertIsNotNone(massage.pk)
        self.assertIsNotNone(massage.conversation)
        
    def test_save_with_parent(self):
        form = ComposeForm(
            {
                'recipient': self.user2.username,
                'subject': 'this is not empty',
                'body': 'this is not empty',
            }, 
            sender=self.user1,
        )
        self.assertTrue(form.is_valid())
        parent_message = form.save()
        message = form.save(parent_message)
        self.assertIsNotNone(message.pk)
        self.assertIsNotNone(message.parent_msg)
        self.assertIsNotNone(message.conversation)
