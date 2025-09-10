from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from .models import *
from django.db.models import Count
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json


def update_head(request, id):
    instance = get_object_or_404(FamilyHead, HeadID=id)
    if request.method == 'POST':
        instance.Name = request.POST.get('head_name')
        instance.Surname = request.POST.get('head_surname')
        instance.Gender = request.POST.get('head_gender')
        instance.Birthdate = request.POST.get('head_birthdate')
        instance.MobileNo = request.POST.get('head_mobile')
        instance.Address = request.POST.get('head_address')
        instance.State = request.POST.get('head_state')
        instance.City = request.POST.get('head_city')
        instance.Pincode = request.POST.get('head_pincode')
        instance.MaritalStatus = request.POST.get('head_marital_status')
        instance.WeddingDate = request.POST.get('head_wedding_date') or None
        instance.Education = request.POST.get('head_education')
        if request.FILES.get('head_photo'):
            instance.Photo = request.FILES.get('head_photo')
        instance.save()

        # Update family members
        members = FamilyMember.objects.filter(HeadID=instance)
        for idx, member in enumerate(members, start=1):
            member.Name = request.POST.get(f'member_{idx}_name')
            member.Surname = request.POST.get(f'member_{idx}_surname')
            member.Birthdate = request.POST.get(f'member_{idx}_birthdate')
            member.MobileNo = request.POST.get(f'member_{idx}_mobile')
            member.Gender = request.POST.get(f'member_{idx}_gender')
            member.Relationship = request.POST.get(f'member_{idx}_relationship')
            member.Address = request.POST.get(f'member_{idx}_address')
            member.State = request.POST.get(f'member_{idx}_state')
            member.City = request.POST.get(f'member_{idx}_city')
            member.Pincode = request.POST.get(f'member_{idx}_pincode')
            # Optionally update photo and hobbies here
            if request.FILES.get(f'member_{idx}_photo'):
                member.Photo = request.FILES.get(f'member_{idx}_photo')
            member.save()

        messages.success(request, 'Head and family updated successfully!')
        return redirect('dashboard')
    states = list(State.objects.filter(country_id=101).values('id', 'name'))
    members = FamilyMember.objects.filter(HeadID=instance)
    return render(request, 'edit_head.html', {'head': instance, 'states': states, 'members': members})
    
# AJAX endpoint for status update
@csrf_exempt
def update_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entry_type = data.get('type')
        entry_id = data.get('id')
        status = data.get('status')
        try:
            if entry_type == 'head':
                obj = FamilyHead.objects.get(HeadID=entry_id)
            elif entry_type == 'member':
                obj = FamilyMember.objects.get(MemberID=entry_id)
            elif entry_type == 'state':
                obj = State.objects.get(id=entry_id)
            elif entry_type == 'city':
                obj = City.objects.get(id=entry_id)
            else:
                return JsonResponse({'success': False, 'error': 'Invalid type'})
            obj.status = status
            obj.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def base(request):
    return render(request, 'base.html')



def stats(request):
    total_families = FamilyHead.objects.count()
    total_members = FamilyMember.objects.count() + FamilyHead.objects.count()
    married_people = FamilyMember.objects.filter(MaritalStatus='Married').count() + FamilyHead.objects.filter(MaritalStatus='Married').count()
    unmarried_people = FamilyMember.objects.filter(MaritalStatus='Unmarried').count() + FamilyHead.objects.filter(MaritalStatus='Unmarried').count()
    active_members = FamilyMember.objects.filter(status=1).count() + FamilyHead.objects.filter(status=1).count()
    total_cities = City.objects.filter(country_id=101).count()


    labels = ['Male', 'Female', 'Other']
    male = FamilyMember.objects.filter(Gender='Male').count() + FamilyHead.objects.filter(Gender='Male').count()
    female = FamilyMember.objects.filter(Gender='Female').count() + FamilyHead.objects.filter(Gender='Female').count()
    other = FamilyMember.objects.filter(Gender='Other').count() + FamilyHead.objects.filter(Gender='Other').count()
    data = [male, female, other]

    context = {
        'total_families': total_families,
        'total_members': total_members,
        'married_people': married_people,
        'unmarried_people': unmarried_people,
        'active_members': active_members,
        'total_cities': total_cities,
        'labels': labels,
        'data': data,
    }
    return render(request, 'stats.html', context)

def home(request):
    return render(request, 'home.html')


def regis(request):
    states = list(State.objects.filter(country_id=101).values('id', 'name'))
    if request.method == 'POST':
        # Family Head
        head = FamilyHead(
            Name=request.POST.get('head_name'),
            Surname=request.POST.get('head_surname'),
            Gender =request.POST.get('head_gender') ,
            Birthdate=request.POST.get('head_birthdate'),
            MobileNo=request.POST.get('head_mobile'),
            Address=request.POST.get('head_address'),
            State=request.POST.get('head_state'),
            City=request.POST.get('head_city'),
            Pincode=request.POST.get('head_pincode'),
            MaritalStatus=request.POST.get('head_marital_status'),
            WeddingDate=request.POST.get('head_wedding_date') or None,
            Education=request.POST.get('head_education'),
            Photo=request.FILES.get('head_photo')
        )
        head.save()

        # Hobbies for Head
        for hobby in request.POST.getlist('head_hobbies[]'):
            if hobby.strip():
                Hobby.objects.create(head=head, Hobby=hobby.strip())

        # Family Members
        member_index = 1
        while True:
            name = request.POST.get(f'member_{member_index}_name')
            if not name:
                break
            address = request.POST.get(f'member_{member_index}_address')
            address_override = bool(address)
            if not address_override:
                # Inherit address from head
                address = head.Address
                state = head.State
                city = head.City
                pincode = head.Pincode
            else:
                state = request.POST.get(f'member_{member_index}_state')
                city = request.POST.get(f'member_{member_index}_city')
                pincode = request.POST.get(f'member_{member_index}_pincode')
            member = FamilyMember(
                HeadID=head,
                Name=name,
                Surname=request.POST.get(f'member_{member_index}_surname'),
                Gender=request.POST.get(f'member_{member_index}_gender'),
                Relationship=request.POST.get(f'member_{member_index}_relationship'),
                Birthdate=request.POST.get(f'member_{member_index}_birthdate'),
                MobileNo=request.POST.get(f'member_{member_index}_mobile'),
                Photo=request.FILES.get(f'member_{member_index}_photo'),
                MaritalStatus=request.POST.get(f'member_{member_index}_marital_status'),
                AddressOverride=address_override,
                Address=address,
                State=state,
                City=city,
                Pincode=pincode,
            )
            member.save()
            # Member hobbies
            for hobby in request.POST.getlist(f'member_{member_index}_hobbies[]'):
                if hobby.strip():
                    Hobby.objects.create(head=head, member=member, Hobby=hobby.strip())
            member_index += 1

        messages.success(request, 'Family registered successfully!')
        return redirect('regis')

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
    total_families = FamilyHead.objects.count()
    total_members = FamilyMember.objects.count() + FamilyHead.objects.count()
    active_members = FamilyMember.objects.filter(status=1).count() + FamilyHead.objects.filter(status=1).count()
    inactive_members = FamilyMember.objects.filter(status=0).count() + FamilyHead.objects.filter(status=0).count()
    deleted = FamilyMember.objects.filter(status=9).count() + FamilyHead.objects.filter(status=9).count()

    tab = request.GET.get('tab', 'head')
    head_page = request.GET.get('head_page', 1)
    family_page = request.GET.get('family_page', 1)
    state_page = request.GET.get('state_page', 1)
    city_page = request.GET.get('city_page', 1)
    search = request.GET.get('search', '').strip()

    tabs = [
        {'key': 'head', 'label': 'Head'},
        {'key': 'family', 'label': 'Family'},
        {'key': 'state', 'label': 'State'},
        {'key': 'city', 'label': 'City'},
    ]

    heads = FamilyHead.objects.all()
    families = FamilyMember.objects.all()
    states = State.objects.all()
    cities = City.objects.all()

    show_all_tables = False
    if search:
        from django.db.models import Q
        heads = heads.filter(Q(Name__icontains=search) | Q(Surname__icontains=search) | Q(MobileNo__icontains=search) | Q(State__icontains=search) | Q(City__icontains=search) | Q(Address__icontains=search))
        families = families.filter(Q(Name__icontains=search) | Q(Surname__icontains=search) | Q(MobileNo__icontains=search) | Q(State__icontains=search) | Q(City__icontains=search) | Q(Address__icontains=search) | Q(Relationship__icontains=search))
        states = states.filter(Q(name__icontains=search))
        cities = cities.filter(Q(name__icontains=search))
        show_all_tables = True

    head_paginator = Paginator(heads, 10)
    family_paginator = Paginator(families, 10)
    state_paginator = Paginator(states, 10)
    city_paginator = Paginator(cities, 10)

    context = {
        'active_tab': tab,
        'tabs': tabs,
        'search': search,
        'show_all_tables': show_all_tables,
        'head_page_obj': head_paginator.get_page(head_page),
        'family_page_obj': family_paginator.get_page(family_page),
        'state_page_obj': state_paginator.get_page(state_page),
        'city_page_obj': city_paginator.get_page(city_page),
        'total_families': total_families,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'deleted': deleted,
        'username': request.user.username if request.user.is_authenticated else '',
    }
    return render(request, 'dashboard.html', context)


def logout_view(request):
    logout(request)
    return redirect('home')



def state(request):
    states = State.objects.all()
    return render(request, 'family_registration.html', {"states": states})

def city(request):
    state_id = request.GET.get("state_id")
    cities = City.objects.filter(state_id=state_id).values("id", "name")
    country_id = request.GET.get("country_id")
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
                'Reset Your Familylink User Password', # email subject
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



