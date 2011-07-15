# -*- coding:utf-8 -*-
import datetime

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from django.core.urlresolvers import reverse
from django.conf import settings

from django_messages.models import Message
from django_messages.forms import ComposeForm
from django_messages.utils import format_quote

def inbox(request, template_name='django_messages/inbox.html', 
    *args, **kwargs):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """
    conversations = Message.objects.inbox_for(request.user)
    return render_to_response(template_name, {
        'conversations': conversations,
    }, context_instance=RequestContext(request))
inbox = login_required(inbox)

def outbox(request, template_name='django_messages/outbox.html', 
    *args, **kwargs):
    """
    Displays a list of sent messages by the current user.
    Optional arguments:
        ``template_name``: name of the template to use.
    """
    conversations = Message.objects.outbox_for(request.user)
    return render_to_response(template_name, {
        'conversations': conversations,
    }, context_instance=RequestContext(request))
outbox = login_required(outbox)

def trash(request, template_name='django_messages/trash.html', 
    *args, **kwargs):
    """
    Displays a list of deleted messages. 
    Optional arguments:
        ``template_name``: name of the template to use
    Hint: A Cron-Job could periodicly clean up old messages, which are deleted
    by sender and recipient.
    """
    conversations = Message.objects.trash_for(request.user)
    return render_to_response(template_name, {
        'conversations': conversations,
    }, context_instance=RequestContext(request))
trash = login_required(trash)

def compose(request, recipient=None, form_class=ComposeForm,
        template_name='django_messages/compose.html', success_url=None, recipient_filter=None,
        *args, **kwargs):
    """
    Displays and handles the ``form_class`` form to compose new messages.
    Required Arguments: None
    Optional Arguments:
        ``recipient``: username of a `django.contrib.auth` User, who should
                       receive the message
        ``form_class``: the form-class to use
        ``template_name``: the template to use
        ``success_url``: where to redirect after successfull submission
    """
    if request.method == "POST":
        form = form_class(request.POST, recipient_filter=recipient_filter, sender=request.user)
        if form.is_valid():
            form.save()
            request.user.message_set.create(
                message=_(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_outbox')
            if request.GET.has_key('next'):
                success_url = request.GET['next']
            return HttpResponseRedirect(success_url)
    else:
        form = form_class(sender=request.user)
        if recipient is not None:
            try:
                form.fields['recipient'].initial = User.objects.get(username=recipient)
            except:
                return HttpResponseRedirect(reverse('messages_compose'))
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))
compose = login_required(compose)

def reply(request, message_id, form_class=ComposeForm,
        template_name='django_messages/compose.html', success_url=None, recipient_filter=None,
        quote=None, 
        *args, **kwargs):
    """
    Prepares the ``form_class`` form for writing a reply to a given message
    (specified via ``message_id``). It uses the ``format_quote`` helper from
    ``messages.utils`` (there is also format_linebreaks_quote defined) to pre-format
    the quote by default but you can use different formater.
    """
    if not quote:
        quote = getattr(settings, 'DJANGO_MESSAGES_QUOTE', format_quote)
    parent = get_object_or_404(Message, id=message_id)
    data = _get_form_data_and_check_parent(request, parent, quote)
    
    if request.method == "POST":
        postdata = request.POST.copy()
        postdata["recipient"] = data["recipient"]
        postdata["subject"] = data["subject"]
        form = form_class(postdata, recipient_filter=recipient_filter, sender=request.user)
        if form.is_valid():
            form.save(parent_msg=parent)
            request.user.message_set.create(
                message=_(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_outbox')
            return HttpResponseRedirect(success_url)
    else:
        form = form_class(data, sender=request.user)
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))
reply = login_required(reply)

def delete(request, success_url=None, *args, **kwargs):
    """
    Marks conversation(s) as deleted. The messages are not
    really removed from the database, because two users must delete a message
    before it's safe to remove it completely. 
    A cron-job should prune the database and remove old messages which are 
    deleted by both users.
    As a side effect, this makes it easy to implement a trash with undelete.
    
    You can pass ?next=/foo/bar/ via the url to redirect the user to a different
    page (e.g. `/foo/bar/`) than ``success_url`` after deletion of the 
    conversation.
    """
    if request.method == 'POST' and 'ids' in request.POST:
        user = request.user
        now = datetime.datetime.now()
        ids = request.POST.getlist('ids')
        queryset = Message.objects.get_conversations(conversations=ids)
        conversation = get_list_or_404(queryset)
        deleted = False
        if success_url is None:
            success_url = reverse('messages_inbox')
        if request.GET.has_key('next'):
            success_url = request.GET['next']
        # FIXME: is there a clean way to combine those 2 requests in one ?
        result1 = queryset.filter(recipient=user).update(recipient_deleted_at=now)
        result2 = queryset.filter(sender=user).update(sender_deleted_at=now)
        if result1 or result2:
            deleted = True    
        if deleted:
            user.message_set.create(message=_(u"Conversation successfully deleted."))
            return HttpResponseRedirect(success_url)
    raise Http404
delete = login_required(delete)

def undelete(request, success_url=None, **kwargs):
    """
    Recovers conversation(s) from trash. This is achieved by removing the
    ``(sender|recipient)_deleted_at`` from the model.
    """
    if request.method == 'POST' and 'ids' in request.POST:
        user = request.user
        ids = request.POST.getlist('ids')
        queryset = Message.objects.get_conversations(conversations=ids)
        undeleted = False
        if success_url is None:
            success_url = reverse('messages_inbox')
        if request.GET.has_key('next'):
            success_url = request.GET['next']
        
        # FIXME: is there a clean way to combine those 2 requests in one ?
        # FIXME: refactor, it's very similar to delete()
        result1 = queryset.filter(recipient=user).update(recipient_deleted_at=None)
        result2 = queryset.filter(sender=user).update(sender_deleted_at=None)
        if result1 or result2:
           undeleted = True    
            
        if undeleted:
            user.message_set.create(message=_(u"Conversation successfully recovered."))
            return HttpResponseRedirect(success_url)
    raise Http404
undelete = login_required(undelete)
    
def _get_form_data_and_check_parent(request, parent, quote):
    if parent.sender != request.user and parent.recipient != request.user:
        raise Http404
    
    if parent.sender == request.user:
        recipient = parent.recipient
    else:
        recipient = parent.sender
        
    data = {
        'body': quote(parent.sender, parent.body),
        'subject': _(u"Re: %(subject)s") % {'subject': parent.subject},
        'recipient': recipient,
    }
    
    return data

def view(request, conversation_id, 
    form_class=ComposeForm, quote=None,
    template_name='django_messages/view.html',
    *args, **kwargs):
    """
    Shows a single conversation.``conversation_id`` argument is required.
    The user is only allowed to see the conversation, if he is either 
    the sender or the recipient. If the user is not allowed a 404
    is raised. 
    If the user is the recipient and the message is unread 
    ``read_at`` is set to the current datetime.
    """
    conversation = Message.objects.get_conversation(conversation=conversation_id)
    if not conversation:
        raise Http404
        
    if not quote:
        quote = getattr(settings, 'DJANGO_MESSAGES_QUOTE', format_quote)
    
    # FIXME: will force query evaluation. Is that a problem ?
    data = _get_form_data_and_check_parent(request, conversation[len(conversation) - 1], quote)
    
    # FIXME This might be costly, since read_at is not indexed
    now = datetime.datetime.now()
    conversation.filter(recipient=request.user, read_at__isnull=True).update(read_at=now)

    return render_to_response(template_name, {
        'conversation': conversation,
        'form' : form_class(data, sender=request.user),
    }, context_instance=RequestContext(request))
view = login_required(view)
