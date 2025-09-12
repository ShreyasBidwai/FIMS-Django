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
from .models import State, City, Country
from django.views.decorators.http import require_http_methods

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter


def pdf_view(request):
    from .models import FamilyHead, FamilyMember
    head_id = request.GET.get('id')
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
    width, height = letter
    y = 60
    c.setFont("Helvetica-Bold", 16)
    if not head_id:
        c.drawString(60, y, "No family selected. Please provide a valid family head ID.")
        c.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="Report.pdf")
    try:
        head = FamilyHead.objects.get(HeadID=head_id)
        members = FamilyMember.objects.filter(HeadID=head)
        c.drawString(60, y, f"Family Report: {head.Name} {head.Surname}")
        y += 30
        c.setFont("Helvetica", 12)
        c.drawString(60, y, f"Head Details:")
        y += 18
        c.drawString(70, y, f"Mobile: {head.MobileNo}, Address: {head.Address}, State: {head.State}, City: {head.City}")
        y += 18
        c.drawString(70, y, f"Pincode: {head.Pincode}, Marital Status: {head.MaritalStatus}, Education: {head.Education}")
        y += 24
        c.setFont("Helvetica-Bold", 14)
        c.drawString(60, y, "Family Members:")
        y += 18
        c.setFont("Helvetica", 12)
        if members:
            for member in members:
                c.drawString(70, y, f"{member.Name} {member.Surname} - {member.Relationship}, Mobile: {member.MobileNo}, State: {member.State}, City: {member.City}")
                y += 16
                if y > height - 40:
                    c.showPage()
                    y = 60
                    c.setFont("Helvetica", 12)
        else:
            c.drawString(70, y, "No family members found.")
    except FamilyHead.DoesNotExist:
        c.drawString(60, y, "Family head not found.")
    c.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"family_report_{headname or 'unknown'}.pdf")


def view_state(request, id):
    from .models import State, City
    state = get_object_or_404(State, id=id)
    search = request.GET.get('search', '').strip()
    cities = state.cities.exclude(status=9)
    if search:
        cities = cities.filter(name__icontains=search)
    return render(request, 'view_state.html', {'state': state, 'cities': cities})

def view_family(request, id):
    head = get_object_or_404(FamilyHead, HeadID=id)
    members = head.familymember_set.all()
    return render(request, 'view_family.html', {'head': head, 'members': members})

@require_http_methods(["GET", "POST"])
def add_state(request):
    error = None
    if request.method == "POST":
        name = request.POST.get("state_name")
        country_id = request.POST.get("country_id") or 101
        if not name:
            error = "State name is required."
        else:
            
            last_state = State.objects.order_by('-id').first()
            next_id = (last_state.id + 1) if last_state else 1
           
            from .models import Country
            india = Country.objects.get(id=101)
            state = State(id=next_id, name=name, status=1, country=india)
            try:
                state.save()
                return redirect('dashboard')
            except Exception as e:
                error = str(e)
    return render(request, 'add_state.html', {'error': error})

from django.views.decorators.http import require_http_methods
@require_http_methods(["GET", "POST"])
def add_city(request):
    error = None
    states = State.objects.filter(country_id=101)
    if request.method == "POST":
        state_id = request.POST.get("state_id")
        city_name = request.POST.get("city_name")
        if not state_id or not city_name:
            error = "State and city name are required."
        else:
            try:
                state = State.objects.get(id=state_id)
                last_city = City.objects.order_by('-id').first()
                next_id = (last_city.id + 1) if last_city else 1
                city = City(id=next_id, name=city_name, state=state, country_id=state.country.id, status=1)
                city.save()
                return redirect('dashboard')
            except Exception as e:
                error = str(e)
    return render(request, 'add_city.html', {'states': states, 'error': error})

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

        # family members
        members = FamilyMember.objects.filter(HeadID=instance)
        for idx, member in enumerate(members, start=1):
            member.Name = request.POST.get(f'member_{idx}_name')
            member.Surname = request.POST.get(f'member_{idx}_surname')
            member.Birthdate = request.POST.get(f'member_{idx}_birthdate')
            member.MobileNo = request.POST.get(f'member_{idx}_mobile')
            member.Gender = request.POST.get(f'member_{idx}_gender')
            member.Relationship = request.POST.get(f'member_{idx}_relationship')
            # Check if 'same address as head' is checked for this member
            if request.POST.get(f'member_{idx}_same_address'):
                member.Address = instance.Address
                member.State = instance.State
                member.City = instance.City
                member.Pincode = instance.Pincode
            else:
                member.Address = request.POST.get(f'member_{idx}_address')
                member.State = request.POST.get(f'member_{idx}_state')
                member.City = request.POST.get(f'member_{idx}_city')
                member.Pincode = request.POST.get(f'member_{idx}_pincode')
            if request.FILES.get(f'member_{idx}_photo'):
                member.Photo = request.FILES.get(f'member_{idx}_photo')
            member.save()

        # Add new members if present in POST data
        existing_count = members.count()
        new_idx = existing_count + 1
        while request.POST.get(f'member_{new_idx}_name'):
            new_member = FamilyMember(
                HeadID=instance,
                Name=request.POST.get(f'member_{new_idx}_name'),
                Surname=request.POST.get(f'member_{new_idx}_surname'),
                Birthdate=request.POST.get(f'member_{new_idx}_birthdate'),
                MobileNo=request.POST.get(f'member_{new_idx}_mobile'),
                Gender=request.POST.get(f'member_{new_idx}_gender'),
                Relationship=request.POST.get(f'member_{new_idx}_relationship'),
                Address=request.POST.get(f'member_{new_idx}_address'),
                State=request.POST.get(f'member_{new_idx}_state'),
                City=request.POST.get(f'member_{new_idx}_city'),
                Pincode=request.POST.get(f'member_{new_idx}_pincode'),
            )
            if request.FILES.get(f'member_{new_idx}_photo'):
                new_member.Photo = request.FILES.get(f'member_{new_idx}_photo')
            new_member.save()
            new_idx += 1

        messages.success(request, 'Head and family updated successfully!')
        return redirect('dashboard')
    states = list(State.objects.filter(country_id=101).values('id', 'name'))
    members = FamilyMember.objects.filter(HeadID=instance)
    return render(request, 'edit_head.html', {'head': instance, 'states': states, 'members': members})


def edit_state(request, id):
    state = get_object_or_404(State, id=id)
    if request.method == 'POST':
        state.name = request.POST.get('name')
        state.save()
        messages.success(request, 'State updated successfully!')
        return redirect('dashboard')
    return render(request, 'edit_state.html', {'state': state})

def edit_city(request, id):
    city = get_object_or_404(City, id=id)
    if request.method == 'POST':
        city.name = request.POST.get('name')
        city.save()
        messages.success(request, 'City updated successfully!')
        return redirect('dashboard')
    return render(request, 'edit_city.html', {'city': city})

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
                obj.status = status
                obj.save()
                if status == 9:
                    # Soft delete all related members
                    FamilyMember.objects.filter(HeadID=obj).update(status=9)
            elif entry_type == 'member':
                obj = FamilyMember.objects.get(MemberID=entry_id)
                obj.status = status
                obj.save()
            elif entry_type == 'state':
                obj = State.objects.get(id=entry_id)
                obj.status = status
                obj.save()
                if status == 9:
         
                    City.objects.filter(state=obj).update(status=9)
            elif entry_type == 'city':
                obj = City.objects.get(id=entry_id)
                obj.status = status
                obj.save()
            else:
                return JsonResponse({'success': False, 'error': 'Invalid type'})
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def base(request):
    return render(request, 'base.html')



def stats(request):
    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    married_people = FamilyMember.objects.exclude(status=9).filter(MaritalStatus='Married').count() + FamilyHead.objects.exclude(status=9).filter(MaritalStatus='Married').count()
    unmarried_people = FamilyMember.objects.exclude(status=9).filter(MaritalStatus='Unmarried').count() + FamilyHead.objects.exclude(status=9).filter(MaritalStatus='Unmarried').count()
    active_members = FamilyMember.objects.exclude(status=9).filter(status=1).count() + FamilyHead.objects.exclude(status=9).filter(status=1).count()
    total_cities = City.objects.exclude(status=9).filter(country_id=101).count()

    labels = ['Male', 'Female', 'Other']
    male = FamilyMember.objects.exclude(status=9).filter(Gender='Male').count() + FamilyHead.objects.exclude(status=9).filter(Gender='Male').count()
    female = FamilyMember.objects.exclude(status=9).filter(Gender='Female').count() + FamilyHead.objects.exclude(status=9).filter(Gender='Female').count()
    other = FamilyMember.objects.exclude(status=9).filter(Gender='Other').count() + FamilyHead.objects.exclude(status=9).filter(Gender='Other').count()
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
    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.filter(status=1).exclude(status=9).count() + FamilyHead.objects.filter(status=1).exclude(status=9).count()
    inactive_members = FamilyMember.objects.filter(status=0).exclude(status=9).count() + FamilyHead.objects.filter(status=0).exclude(status=9).count()
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

    heads = FamilyHead.objects.exclude(status=9)
    families = FamilyMember.objects.exclude(status=9)
    states = State.objects.exclude(status=9) if hasattr(State, 'status') else State.objects.all()
    all_states = State.objects.exclude(status=9)
    state_filter = request.GET.get('state_filter', '')
    if state_filter:
        filtered_cities = City.objects.exclude(status=9).filter(state_id=state_filter)
    else:
        filtered_cities = City.objects.exclude(status=9)

    show_all_tables = False
    if search:
        from django.db.models import Q
        heads = heads.filter(Q(Name__icontains=search) | Q(Surname__icontains=search) | Q(MobileNo__icontains=search) | Q(State__icontains=search) | Q(City__icontains=search) | Q(Address__icontains=search))
        families = families.filter(Q(Name__icontains=search) | Q(Surname__icontains=search) | Q(MobileNo__icontains=search) | Q(State__icontains=search) | Q(City__icontains=search) | Q(Address__icontains=search) | Q(Relationship__icontains=search))
        states = states.filter(Q(name__icontains=search))
        filtered_cities = filtered_cities.filter(Q(name__icontains=search))
        show_all_tables = True

    head_paginator = Paginator(heads, 10)
    family_paginator = Paginator(families, 10)
    state_paginator = Paginator(states, 10)
    city_paginator = Paginator(filtered_cities, 10)

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
        'all_states': all_states,
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



