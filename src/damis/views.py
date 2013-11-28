#! coding: utf-8
import json
import re
from os.path import join, exists, getsize, splitext
from os import makedirs, listdir
from subprocess import Popen, PIPE

from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.forms.models import modelformset_factory
from django.forms.models import inlineformset_factory
from django.core.context_processors import csrf

from damis.forms import LoginForm
from damis.forms import DatasetForm
from damis.forms import AlgorithmForm
from damis.forms import ParameterForm, ParameterFormset
from damis.forms import ExperimentForm
from damis.forms import TaskFormset, CreateExperimentFormset, ParameterValueFormset, ParameterValueForm
from damis.forms import DatasetSelectForm


from damis.utils import slugify

from damis.models import Algorithm
from damis.models import Parameter, ParameterValue
from damis.models import Dataset
from damis.models import DatasetLicense
from damis.models import Experiment
from damis.models import Task


class LoginRequiredMixin(object):
    pass
    # @method_decorator(login_required(login_url=reverse_lazy('login')))
    # def dispatch(self, *args, **kwargs):
    #     return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)

def index_view(request):
    return HttpResponseRedirect(reverse_lazy('experiment-list'))

def about_view(request):
    return render(request, 'index.html', {})

def help_view(request):
    return render(request, 'base.html', {})

class DatasetCreate(LoginRequiredMixin, CreateView):
    model = Dataset
    template_name = 'damis/dataset_new.html'
    form_class = DatasetForm

    def form_valid(self, form):
        form.instance.slug = slugify(form.instance.title)
        return super(DatasetCreate, self).form_valid(form)

class DatasetList(LoginRequiredMixin, ListView):
    model = Dataset
    paginate_by = 50
    template_name = 'damis/dataset_list.html'

    def get_queryset(self):
        qs = super(DatasetList, self).get_queryset()
        return qs.order_by('-created')

class DatasetUpdate(LoginRequiredMixin, UpdateView):
    model = Dataset

class DatasetDetail(LoginRequiredMixin, DetailView):
    model = Dataset

class DatasetDelete(LoginRequiredMixin, DeleteView):
    model = Dataset
    success_url = reverse_lazy('dataset-list')


class AlgorithmCreate(LoginRequiredMixin, CreateView):
    model = Algorithm
    form_class = AlgorithmForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        parameter_form =  ParameterFormset()
        return self.render_to_response(
                self.get_context_data(form=form,
                    parameter_form=parameter_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        parameter_form = ParameterFormset(self.request.POST)
        if form.is_valid() and parameter_form.is_valid():
            return self.form_valid(form, parameter_form)
        else:
            return self.form_invalid(form, parameter_form)

    def form_valid(self, form, parameter_form):
        self.object = form.save()
        parameter_form.instance = self.object
        parameter_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, parameter_form):
        return self.render_to_response(self.get_context_data(form=form,
            parameter_form=parameter_form))


class AlgorithmList(LoginRequiredMixin, ListView):
    model = Algorithm

class AlgorithmUpdate(LoginRequiredMixin, UpdateView):
    model = Algorithm
    form_class = AlgorithmForm

    def post(self, request, *args, **kwargs):
        self.object = Algorithm.objects.get(pk=self.kwargs['pk'])
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        parameter_form = ParameterFormset(self.request.POST, instance=self.object)
        if form.is_valid() and parameter_form.is_valid():
            return self.form_valid(form, parameter_form)
        else:
            return self.form_invalid(form, parameter_form)

    def form_valid(self, form, parameter_form):
        self.object = form.save()
        parameter_form.instance = self.object
        parameter_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, parameter_form):
        return self.render_to_response(self.get_context_data(form=form,
            parameter_form=parameter_form))

    def get_context_data(self, **kwargs):
        context = super(AlgorithmUpdate, self).get_context_data(**kwargs)
        ParameterFormset = inlineformset_factory(Algorithm, Parameter, extra=0, can_delete=True)
        context['parameter_form'] = ParameterFormset(instance=self.object)
        return context

class AlgorithmDetail(LoginRequiredMixin, DetailView):
    model = Algorithm

class AlgorithmDelete(LoginRequiredMixin, DeleteView):
    model = Algorithm
    success_url = reverse_lazy('algorithm-list')


class ExperimentList(LoginRequiredMixin, ListView):
    model = Experiment

class ExperimentDetail(LoginRequiredMixin, DetailView):
    model = Experiment

class ExperimentDelete(LoginRequiredMixin, DeleteView):
    model = Experiment
    success_url = reverse_lazy('experiment-list')

class ExperimentUpdate(LoginRequiredMixin, UpdateView):
    model = Experiment

    def get(self, request, *args, **kwargs):
        self.object = None
        experiment = get_object_or_404(Experiment, pk=self.kwargs['pk'])
        task_formset = TaskFormset(instance=experiment)
        return self.render_to_response(self.get_context_data(
                    experiment=task_formset.instance,
                    task_formset=task_formset,
                ))

    def post(self, request, *args, **kwargs):
        self.object = None
        instance = Experiment.objects.get(pk=self.kwargs['pk'])

        task_formset = TaskFormset(self.request.POST, instance=instance)
        if task_formset.is_valid():
            return self.form_valid(task_formset)
        else:
            return self.form_invalid(task_formset)

    def form_valid(self, task_formset):
        self.object = task_formset.save_all()
        return HttpResponseRedirect(reverse_lazy('experiment-list'))

    def form_invalid(self, task_formset):
        return self.render_to_response(self.get_context_data(
                        experiment=task_formset.instance,
                        task_formset=task_formset,
                    ))


class ExperimentCreate(LoginRequiredMixin, CreateView):
    model = Experiment
    template_name = 'damis/experiment_create.html'

    def get(self, request, *args, **kwargs):
        self.object = None

        experiment_pk = self.kwargs.get('pk')
        if experiment_pk:
            experiment = Experiment.objects.get(pk=experiment_pk)
        else:
            experiment = Experiment()

        experiment_form = ExperimentForm(instance=experiment)
        task_formset = CreateExperimentFormset(instance=experiment)

        # Move one extra empty task formset to the begining of forms
        form_count = len(task_formset.forms)
        task_formset.forms.insert(0, task_formset.forms.pop(form_count - 1))

        return self.render_to_response(self.get_context_data(
                    experiment=task_formset.instance,
                    task_formset=task_formset,
                    experiment_form=experiment_form,
                ))

    def get_context_data(self, **kwargs):
        context = super(ExperimentCreate, self).get_context_data(**kwargs)
        context['dataset_form'] = DatasetSelectForm()
        context.update(csrf(self.request))
        return context

    def post(self, request, *args, **kwargs):
        self.object = None

        experiment_form = ExperimentForm(self.request.POST)
        task_formset = CreateExperimentFormset(self.request.POST)

        skip_validation = self.request.POST.get('skip_validation')
        if skip_validation:
            experiment_form.full_clean()
            exp_data = experiment_form.cleaned_data
            exp_data.pop('skip_validation')
            exp= Experiment(**exp_data)
            exp.save()
            return HttpResponse(reverse_lazy('experiment-update', kwargs={'pk': exp.pk}))

        if experiment_form.is_valid() and task_formset.is_valid():
            return self.form_valid(experiment_form, task_formset)
        else:
            return self.form_invalid(experiment_form, task_formset)

    def form_valid(self, experiment_form, task_formset):
        exp = experiment_form.save()
        self.object = task_formset.save_all(experiment=exp)

        # run_exp_cmd = "bin/fab run_experiment:%s -H %s@uosis.mif.vu.lt -p %s" % (
        #         experiment.pk,
        #         self.request.user.username,
        #         self.request.session['password'])
        # shell_response = Popen(run_exp_cmd, shell=True)

        return HttpResponse(reverse_lazy('experiment-update', kwargs={'pk': exp.pk}))

    def form_invalid(self, experiment_form, task_formset):
        return render_to_response('damis/_experiment_form.html',
                        self.get_context_data(
                            experiment=task_formset.instance,
                            task_formset=task_formset,
                            experiment_form=experiment_form,
                        ))


def gen_parameter_prefixes(request):
    prefixes = request.GET.getlist('prefixes[]')
    task_prefixes = [re.findall('(tasks-\d+)', prefix)[0] for prefix in prefixes]
    pv_prefixes = ['PV_' + str(hash(prefix)) for prefix in task_prefixes]
    return HttpResponse(",".join(pv_prefixes))

def algorithm_parameter_form(request):
    algorithm = get_object_or_404(Algorithm, pk=request.GET.get('algorithm_id'))
    task_form_prefix = re.findall('[id_]*(\w+-\d+)', request.GET.get('prefix'))[0]
    prefix = 'PV_%s' % hash(task_form_prefix)

    ParameterValueFormset = inlineformset_factory(Task,
                                ParameterValue,
                                form=ParameterValueForm,
                                extra=len(algorithm.parameters.all()),
                                can_delete=False
                            )
    parameter_formset = ParameterValueFormset(instance=None, prefix=prefix)
    for parameter, form in zip(algorithm.parameters.all(), parameter_formset.forms):
        form.initial = {'parameter': parameter}

    return render_to_response('dynamic/parameter_form.html', {
        'formset': parameter_formset,
        })



class DatasetLicenseCreate(LoginRequiredMixin, CreateView):
    model = DatasetLicense
    template_name = 'damis/obj_form.html'


## User views
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            if user is not None and user.is_active:
                request.session['password'] = form.cleaned_data['password']
                login(request, user)
                return HttpResponseRedirect(reverse_lazy('home'))
    else:
        form = LoginForm()

    return render(request, 'login.html', {
            'form': form,
        })

def logout_view(request):
    logout(request)
    request.session.clear()
    return HttpResponseRedirect('/login/')
