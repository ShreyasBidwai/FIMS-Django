from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def regis(request):
    return render(request, 'registration.html')

def login(request):
    return render(request, 'login.html', name=login)