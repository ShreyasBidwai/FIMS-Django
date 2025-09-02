from django.shortcuts import render

def regis(request):
    return render(request, 'registration.html')