# -*- coding:utf-8 -*-
from datetime import datetime
from optparse import make_option
from time import time

from django.core.management.base import BaseCommand
from django.conf import settings

from django_messages.models import Message


class Command(BaseCommand):
    """Delete messages that were deleted by both sender and recipient"""
    help = __doc__

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Count the number of messages that would be deleted without actually doing it'),
        )

    def handle(self, *args, **options):
        dryrun = options['dryrun']
        
        limit = time() - settings.DELETED_MESSAGE_MAX_AGE
        limit = datetime.fromtimestamp(limit)
        query = Message.objects.filter(
            sender_deleted_at__lte=limit,
            recipient_deleted_at__lte=limit
        )
        if dryrun:
            count = query.count()
            print 'Total count of messages to be deleted: %d' % count
        else:
            query.delete()
