from collections import namedtuple

from django import forms
from django.test import TestCase
from django.contrib.auth.models import User
from django_messages.fields import CommaSeparatedUserInput, BaseUserField


MockUserObject = namedtuple('MockUserObject', ['username'])


class CommaSeparatedUserInputTests(TestCase):
    
    def test_render_widget_with_empty_value(self):
        widget = CommaSeparatedUserInput()
        input_name = 'recipient'
        input_value = None
        html = widget.render(input_name, input_value, {'extra_attribute':'extra_value'})
        expected_html = u'<input extra_attribute="extra_value" '
        expected_html += u'type="text" name="recipient" />'
        self.assertEquals(expected_html, html)
        
    def test_render_widget_with_value(self):
        widget = CommaSeparatedUserInput()
        input_name = 'recipient'
        input_value = 'username'
        html = widget.render(input_name, input_value, {'extra_attribute':'extra_value'})
        expected_html = u'<input extra_attribute="extra_value" '
        expected_html += u'type="text" name="recipient" value="username" />'
        self.assertEquals(expected_html, html)

    def test_render_widget_with_list_with_one_object(self):
        mock_user = MockUserObject(username='username_mock_user')
        widget = CommaSeparatedUserInput()
        input_name = 'recipient'
        input_value = [mock_user]
        html = widget.render(input_name, input_value, {'extra_attribute':'extra_value'})
        expected_html = u'<input extra_attribute="extra_value" '
        expected_html += u'type="text" name="recipient" value="username_mock_user" />'
        self.assertEquals(expected_html, html)

    def test_render_widget_with_list_with_several_object(self):
        mock_user1 = MockUserObject(username='username_mock_user_1')
        mock_user2 = MockUserObject(username='username_mock_user_2')
        widget = CommaSeparatedUserInput()
        input_name = 'recipient'
        input_value = [mock_user1, mock_user2]
        html = widget.render(input_name, input_value, {'extra_attribute':'extra_value'})
        expected_html = u'<input extra_attribute="extra_value" '
        expected_html += u'type="text" name="recipient" '
        expected_html += u'value="username_mock_user_1, username_mock_user_2" />'
        self.assertEquals(expected_html, html)

    def test_render_widget_with_tuple_with_one_object(self):
        mock_user = MockUserObject(username='username_mock_user')
        widget = CommaSeparatedUserInput()
        input_name = 'recipient'
        input_value = (mock_user,)
        html = widget.render(input_name, input_value, {'extra_attribute':'extra_value'})
        expected_html = u'<input extra_attribute="extra_value" '
        expected_html += u'type="text" name="recipient" value="username_mock_user" />'
        self.assertEquals(expected_html, html)

    def test_render_widget_with_tuple_with_several_object(self):
        mock_user1 = MockUserObject(username='username_mock_user_1')
        mock_user2 = MockUserObject(username='username_mock_user_2')
        widget = CommaSeparatedUserInput()
        input_name = 'recipient'
        input_value = (mock_user1, mock_user2)
        html = widget.render(input_name, input_value, {'extra_attribute':'extra_value'})
        expected_html = u'<input extra_attribute="extra_value" '
        expected_html += u'type="text" name="recipient" '
        expected_html += u'value="username_mock_user_1, username_mock_user_2" />'
        self.assertEquals(expected_html, html)


class CommaSeparatedUserFieldTests(TestCase):
    pass # Not used in current django_messages


class BaseUserFieldTests(TestCase):
    
    def setUp(self):
        self.field = BaseUserField()
    
    def test_no_such_user(self):
        with self.assertRaises(forms.ValidationError) as context_manager:
            self.field.clean('foobarbaz')
        exception = context_manager.exception
        self.assertEquals(1, len(exception.messages))
        self.assertEquals(u'There is no user with this username.',
                          exception.messages[0])
        
    def test_user_exists(self):
        user = User.objects.create(username="foobarbaz")
        self.assertEquals(user, self.field.clean(user.username))

    def test_user_filtered(self):
        user = User.objects.create(username="foobarbaz")
        def filter_all_users(username):
            return False
        self.field = BaseUserField(recipient_filter=filter_all_users)
        with self.assertRaises(forms.ValidationError) as context_manager:
            self.field.clean('foobarbaz')
        exception = context_manager.exception
        self.assertEquals(1, len(exception.messages))
        self.assertEquals(u'There is no user with this username.',
                          exception.messages[0])

