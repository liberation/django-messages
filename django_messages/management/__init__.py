from django.db.models import get_models, signals
from django.conf import settings
from django.utils.translation import ugettext_noop as _

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("messages_received", _("Message Received"), _("You have received a message"), default=2)
        notification.create_notice_type("messages_sent", _("Message Sent"), _("You have sent a message"), default=1)
        notification.create_notice_type("messages_replied", _("Message Replied"), _("You have replied to a message"), default=1)
        notification.create_notice_type("messages_reply_received", _("Reply Received"), _("You have received a reply to a message"), default=2)
#        notification.create_notice_type("messages_deleted", _("Message Deleted"), _("You have deleted a message"), default=1)
#        notification.create_notice_type("messages_recovered", _("Message Recovered"), _("You have undeleted a message"), default=1)

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
