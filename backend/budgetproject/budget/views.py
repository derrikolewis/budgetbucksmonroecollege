from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from .models import Project, Category, Expense
from django.views.generic import CreateView
from django.utils.text import slugify
from .forms import ExpenseForm, CreateUserForm
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

def home(request):
    context = {}
    return render(request, 'budget/base.html', context)

def registerPage(request):
	if request.user.is_authenticated:
		return redirect('list')
	else:
		form = CreateUserForm()
		if request.method == 'POST':
			form = CreateUserForm(request.POST)
			if form.is_valid():
				form.save()
				user = form.cleaned_data.get('username')
				messages.success(request, 'Account was created for ' + user)

				return redirect('login')
			

		context = {'form':form}
		return render(request, 'budget/register.html', context)
def loginPage(request):
	if request.user.is_authenticated:
		return redirect('list')
	else:
		if request.method == 'POST':
			username = request.POST.get('username')
			password =request.POST.get('password')

			user = authenticate(request, username=username, password=password)

			if user is not None:
				login(request, user)
				return redirect('list')
			else:
				messages.info(request, 'Username OR password is incorrect')

		context = {}
		return render(request, 'budget/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def project_list(request):
    project_list = Project.objects.all()
    return render(request, 'budget/project-list.html', {'project_list': project_list})

@login_required(login_url='login')
def project_detail(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)

    if request.method == 'GET':
        category_list = Category.objects.filter(project=project)
        return render(request, 'budget/project-detail.html', {'project': project, 'expense_list': project.expenses.all(), 'category_list': category_list})

    elif request.method == 'POST':
        # process the form
        form = ExpenseForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            amount = form.cleaned_data['amount']
            category_name = form.cleaned_data['category']

            category = get_object_or_404(Category, project=project, name=category_name)

            Expense.objects.create(
                project=project,
                title=title,
                amount=amount,
                category=category
            ).save()

    elif request.method == 'DELETE':
        id = json.loads(request.body)['id']
        expense = Expense.objects.get(id=id)
        expense.delete()

        return HttpResponse('')

    return HttpResponseRedirect(project_slug)


class ProjectCreateView(LoginRequiredMixin, CreateView, HttpRequest, HttpResponse):
    login_url = 'login'
    model = Project
    template_name = 'budget/add-project.html'
    fields = ('name', 'budget', 'user')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        HttpResponse.user.Project.add(self)

        categories = self.request.POST['categoriesString'].split(',')
        for category in categories:
            Category.objects.create(
                project=Project.objects.get(id=self.object.id),
                name=category
            ).save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return slugify(self.request.POST['name'])