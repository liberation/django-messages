VERSION = (0, 5, 0, 'pre')
__version__ = '.'.join(map(str, VERSION))

from django.db.models import signals
from django_messages.models import Message
from django.conf import settings

notification = False
if 'notification' in settings.INSTALLED_APPS:
    from notification import models as notification

def message_post_save_callback(sender, instance, created, **kwargs):
    if notification and created:
        if instance.parent_msg:
            notification.send([instance.sender], "messages_replied", {'message': instance,})
            notification.send([instance.recipient], "messages_reply_received", {'message': instance,})
        else:
            notification.send([instance.sender], "messages_sent", {'message': instance,})
            notification.send([instance.recipient], "messages_received", {'message': instance,})
signals.post_save.connect(message_post_save_callback, sender=Message)
