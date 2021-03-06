"""
Based on http://www.djangosnippets.org/snippets/595/
by sopelkin
and http://www.djangosnippets.org/snippets/1196/
by sma
"""

from django import forms
from django.conf import settings
from django.forms import widgets
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

if "relationships" in settings.INSTALLED_APPS and "ajax_select" in settings.INSTALLED_APPS:
    from ajax_select.fields import AutoCompleteField
else:
    AutoCompleteField = None

class CommaSeparatedUserInput(widgets.Input):
    input_type = 'text'
    
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, (list, tuple)):
            value = (', '.join([user.username for user in value]))
        return super(CommaSeparatedUserInput, self).render(name, value, attrs)
        


class CommaSeparatedUserField(forms.Field):
    widget = CommaSeparatedUserInput
    
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        self._recipient_filter = recipient_filter
        super(CommaSeparatedUserField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        super(CommaSeparatedUserField, self).clean(value)
        if not value:
            return ''
        if isinstance(value, (list, tuple)):
            return value
        
        names = set(value.split(','))
        names_set = set([name.strip() for name in names])
        users = list(User.objects.filter(username__in=names_set))
        unknown_names = names_set ^ set([user.username for user in users])
        
        recipient_filter = self._recipient_filter
        invalid_users = []
        if recipient_filter is not None:
            for r in users:
                if recipient_filter(r) is False:
                    users.remove(r)
                    invalid_users.append(r.username)
        
        if unknown_names or invalid_users:
            raise forms.ValidationError(_(u"The following usernames are incorrect: %(users)s") % {'users': ', '.join(list(unknown_names)+invalid_users)})
        
        return users

class BaseUserField(forms.CharField): 
    widget = widgets.TextInput
    
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        self._recipient_filter = recipient_filter
        super(BaseUserField, self).__init__(*args, **kwargs)
        
    def clean(self, value): 
        value = super(BaseUserField, self).clean(value) 
        if not value: 
            return None 
        try:
            user = User.objects.get(username=value) 
            recipient_filter = self._recipient_filter
            if recipient_filter is not None:
                if not recipient_filter(user):
                    raise forms.ValidationError(_(u"There is no user with this username."))
            return user
        except User.DoesNotExist: 
            raise forms.ValidationError(_(u"There is no user with this username."))

if AutoCompleteField:
    class UserField(BaseUserField, AutoCompleteField):
        def __init__(self, *args, **kwargs):
            args = ('following',)
            super(UserField, self).__init__(*args, **kwargs)
else:
    UserField = BaseUserField

    
