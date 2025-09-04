from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from .models import *
import execjs



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
            # Pass error_message for client-side display
            return render(request, 'login.html', {'error_message': 'Invalid credentials or not a superuser', 'username': username})

    return render(request, 'login.html')

def resetPassword(request):
    return render(request, 'resetPassword.html')

@login_required(login_url='login')
def dashboard(request):
    # def product_list(request):
    # # Retrieve all products
    # all_products = Product.objects.all()

    # # Retrieve a specific product by its primary key
    # # product = Product.objects.get(pk=1)

    # # Retrieve products based on specific criteria
    # # electronics_products = Product.objects.filter(category='electronics')

    # # Order the results
    # # ordered_products = Product.objects.order_by('name')

    # context = {'products': all_products} # Or other QuerySets
    
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


def ForgotPassword(request):

    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})

            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            email_body = f'Reset FIMS your password using the link below:\n\n\n{full_password_reset_url}'
        
            email_message = EmailMessage(
                'Reset Your FIMS User Password', # email subject
                email_body,
                settings.EMAIL_HOST_USER, # email sender
                [email] # email  receiver 
            )

            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'forgot_password.html')

def PasswordResetSent(request, reset_id):

    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'password_reset_sent.html')
    else:
        # redirect to forgot password page if code does not exist
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

def ResetPassword(request, reset_id):

    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            errors = []

            if password != confirm_password:
                errors.append('Passwords do not match')
            if not password or len(password) < 5:
                errors.append('Password must be at least 5 characters long')

            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)
            if timezone.now() > expiration_time:
                errors.append('Reset link has expired')
                password_reset_id.delete()

            if not errors:
                user = password_reset_id.user
                user.set_password(password)
                user.save()
                password_reset_id.delete()
                
                return redirect('login_view')
            else:
                for error in errors:
                    messages.error(request, error)
                return redirect('reset-password', reset_id=reset_id)

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'reset_password.html')