from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from vanilla import CreateView, ListView, UpdateView, DetailView

from .models import Event, Proposal, Vote
from .forms import EventForm, ProposalForm


class BaseEventView(object):
    model = Event
    form_class = EventForm
    lookup_field = 'slug'


class ListEvents(BaseEventView, ListView):
    template_name = 'event/event_list.html'


class CreateEvent(BaseEventView, CreateView):
    template_name = 'event/event_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        messages.success(self.request, _('Event created.'))
        return HttpResponseRedirect(self.get_success_url())


class DetailEvent(BaseEventView, DetailView):
    template_name = 'event/event_detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailEvent, self).get_context_data(**kwargs)
        context['vote_rates'] = Vote.VOTE_RATES
        return context


class UpdateEvent(BaseEventView, UpdateView):
    template_name = 'event/event_form.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Event updated.'))
        return HttpResponseRedirect(self.get_success_url())


class BaseProposalView(object):
    model = Proposal
    form_class = ProposalForm
    lookup_field = 'slug'


class CreateProposal(BaseProposalView, CreateView):
    template_name = 'proposal/proposal_form.html'

    def get_context_data(self, **kwargs):
        kwargs['event'] = Event.objects.get(slug=self.kwargs['slug'])
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.event = Event.objects.get(slug=self.kwargs['slug'])
        self.object.save()
        messages.success(self.request, _('Proposal created.'))
        return HttpResponseRedirect(self.get_success_url())


class UpdateProposal(BaseProposalView, UpdateView):
    template_name = 'proposal/proposal_form.html'

    def get_context_data(self, **kwargs):
        kwargs['event'] = Event.objects.get(slug=self.kwargs['event_slug'])
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Proposal updated.'))
        return HttpResponseRedirect(self.get_success_url())


class RateProposal(BaseProposalView, UpdateView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        rate = kwargs.get('rate')
        try:
            rate_int = [r[0] for r in Vote.VOTE_RATES if rate in r][0]
            self.object.votes.create(user=request.user, rate=rate_int)
        except IndexError:
            messages.error(self.request, _('Rate Index not found.'))
        except (IntegrityError, ValidationError), e:
            messages.error(self.request, e.message)
        else:
            messages.success(self.request, _('Proposal rated.'))
        return HttpResponseRedirect(self.get_success_url())
