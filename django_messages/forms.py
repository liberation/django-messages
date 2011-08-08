import datetime
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.contrib.auth.models import User

if "relationships" in settings.INSTALLED_APPS:
    from relationships.models import RelationshipStatus
    relationships = True
else:
    relationships = False

from django_messages.models import Message
from django_messages.fields import UserField

class ComposeForm(forms.Form):
    """
    A simple default form for private messages.
    """
    recipient = UserField(label=_(u"Recipient"))
    subject = forms.CharField(label=_(u"Subject"))
    body = forms.CharField(label=_(u"Body"),
    widget=forms.Textarea(attrs={'rows': '12', 'cols':'55'}))
    
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        sender = kwargs.pop('sender', None)
        super(ComposeForm, self).__init__(*args, **kwargs)
        if recipient_filter is not None:
            self.fields['recipient']._recipient_filter = recipient_filter
        if sender:
            self.sender = sender
            
    def clean_subject(self):
        return self.cleaned_data['subject'][:120]
            
    def clean(self):
        if not self.sender:
            raise forms.ValidationError(_(u"Unknown user")) 
        return self.cleaned_data

    def clean_recipient(self):
        # Note: We can't do this in fields.py because we need the sender
        recipient = self.cleaned_data['recipient']
        if relationships and recipient.relationships.exists(self.sender, RelationshipStatus.objects.get(from_slug="blocking")):
            raise forms.ValidationError(
                _(u"%(recipient)s has blacklisted you, you can't message him any more.") % 
                { 'recipient' : recipient }) 
        return recipient
                
    def save(self, parent_msg=None):
        # recipients = self.cleaned_data['recipient']
        recipient = self.cleaned_data['recipient']
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']
        # for r in recipients:
        r = recipient
        if True:
            msg = Message(
                sender = self.sender,
                recipient = r,
                subject = subject,
                body = body,
            )
            if parent_msg is not None:
                msg.parent_msg = parent_msg
                parent_msg.replied_at = datetime.datetime.now()
                parent_msg.save()
                msg.conversation = parent_msg.conversation
            msg.save()
            # FIXME: workaround to make sure msg.conversation is saved
            #        even when creating a new conversation
            if not msg.conversation:
                msg.conversation = msg
                msg.save()
        return msg
