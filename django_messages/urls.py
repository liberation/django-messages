from django.conf.urls import url
from django.conf.urls import patterns
from django.views.generic.base import RedirectView

from django_messages.views import *

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='inbox/'), name='messages_index'),
    url(r'^inbox/$', inbox, name='messages_inbox'),
    url(r'^outbox/$', outbox, name='messages_outbox'),
    url(r'^compose/$', compose, name='messages_compose'),
    url(r'^compose/(?P<recipient>[\w.@+-]+)/$', compose, name='messages_compose_to'),
    url(r'^reply/(?P<message_id>[\d]+)/$', reply, name='messages_reply'),
    url(r'^view/(?P<conversation_id>[\d]+)/$', view, name='messages_detail'),
    url(r'^delete$', delete, name='messages_delete'),
    url(r'^undelete$', undelete, name='messages_undelete'),
    url(r'^trash/$', trash, name='messages_trash'),
)
