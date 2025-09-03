from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from .models import State, City



def home(request):
    return render(request, 'home.html')


def regis(request):
    states = list(State.objects.filter(country_id=101).values('id', 'name'))
    return render(request, 'registration.html', {'states': states})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser: 
            login(request, user)
            return redirect('dashboard')
        else:
            return render(
                request,
                'login.html',
                {'error_message': 'Invalid credentials or not a superuser'}
            )

    return render(request, 'login.html')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard.html', {'username': request.user.username})


def logout_view(request):
    logout(request)
    return redirect('login_view')



def state(request):
    states = State.objects.all()
    return render(request, 'family_registration.html', {"states": states})

def city(request):
    state_id = request.GET.get("state_id")
    cities = City.objects.filter(state_id=state_id).values("id", "name")
    return JsonResponse(list(cities), safe=False)
