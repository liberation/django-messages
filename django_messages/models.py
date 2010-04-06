import datetime
from django.db import models
from django.conf import settings
from django.db.models import signals, Max
from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class MessageManager(models.Manager):

    @property
    def related(self):
        return self.select_related('recipient', 'sender')

    @property
    def _conversations(self):
        """
        Returns latest message id for each conversations
        """
        return self.values(
            'conversation'
        ).annotate(
            Max('id')
        ).values_list(
            'id__max', 
            flat=True
        ).order_by(
            'conversation'
        )

    def inbox_for(self, user):
        """
        Return Inbox by filtering conversations containing messages
        received by given user that were not deleted
        """
        return self.related.filter(
            id__in=self._conversations.filter(
                recipient=user, 
                recipient_deleted_at__isnull=True
            )
        )

    def outbox_for(self, user):
        """
        Return Outbox by filtering conversations containing messages 
        sent by given user that were not deleted
        """
        return self.related.filter(
            id__in=self._conversations.filter(
                sender=user,
                sender_deleted_at__isnull=True,
            )
        )

    def trash_for(self, user):
        """
        Return Trash by filtering conversations containing messages 
        sent by given user that were deleted
        """
        tmp = self._conversations.filter(
                sender=user,
                sender_deleted_at__isnull=False,
        ) | self._conversations.filter(
                recipient=user,
                recipient_deleted_at__isnull=False,
        )
        return self.related.filter(
            id__in=tmp
        )
        
    def get_conversation(self, conversation):
        """
        Returns a specific conversation. We don't filter by user here,
        since we have the conversation id. The view should check the 
        recipient/sender fields if necessary.        
        """
        return self.related.filter(
            conversation=conversation
        ).order_by('sent_at')
        
    def get_conversations(self, conversations):
        """
        Returns specific conversations. We don't filter by user here,
        since we have the conversations id. The view should check the 
        recipient/sender fields if necessary.        
        """
        return self.related.filter(
            conversation__in=conversations
        ).order_by('sent_at')


class Message(models.Model):
    """
    A private message from user to user
    """
    subject = models.CharField(_("Subject"), max_length=120)
    body = models.TextField(_("Body"))
    sender = models.ForeignKey(User, related_name='sent_messages', null=True, verbose_name=_("Sender"))
    recipient = models.ForeignKey(User, related_name='received_messages', null=True, verbose_name=_("Recipient"))
    parent_msg = models.ForeignKey('self', related_name='next_messages', null=True, blank=True, verbose_name=_("Parent message"))
    conversation = models.ForeignKey('self', null=True, blank=True, verbose_name=_("Conversation"))
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)
    replied_at = models.DateTimeField(_("replied at"), null=True, blank=True)
    sender_deleted_at = models.DateTimeField(_("Sender deleted at"), null=True, blank=True)
    recipient_deleted_at = models.DateTimeField(_("Recipient deleted at"), null=True, blank=True)
    
    objects = MessageManager()
    
    def new(self):
        """returns whether the recipient has read the message or not"""
        if self.read_at is not None:
            return False
        return True
        
    def replied(self):
        """returns whether the recipient has written a reply to this message"""
        if self.replied_at is not None:
            return True
        return False
    
    def __unicode__(self):
        return self.subject
    
    def get_absolute_url(self):
        return ('messages_detail', [self.conversation_id])
    get_absolute_url = models.permalink(get_absolute_url)
    
    def save(self, **kwargs):
        if not self.id:
            self.sent_at = datetime.datetime.now()
        super(Message, self).save(**kwargs)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        
def inbox_count_for(user):
    """
    returns the number of unread messages for the given user but does not
    mark them seen
    """
    return Message.objects.filter(recipient=user, read_at__isnull=True, recipient_deleted_at__isnull=True).count()

# fallback for email notification if django-notification could not be found
if "notification" not in settings.INSTALLED_APPS:
    from django_messages.utils import new_message_email
    signals.post_save.connect(new_message_email, sender=Message)
