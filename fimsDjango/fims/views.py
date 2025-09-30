from django.db import models
from django.http import FileResponse, JsonResponse
import io
from openpyxl import Workbook
from openpyxl.styles import Font
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_http_methods
from .models import FamilyHead, FamilyMember, State, City, Country, Hobby, AdminLog, PasswordReset
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
import datetime
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .utils import decode_id
from .models import *



@require_GET
def dashboard_stats_api(request):
    # Get stats for dashboard cards
    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.filter(status=1).count()
    inactive_members = FamilyMember.objects.filter(status=0).count()
    return JsonResponse({
        'total_families': total_families,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
    })

@require_GET
def export_heads_excel(request):

    search = request.GET.get('search', '').strip()

    
    heads = FamilyHead.objects.exclude(status=9)

    
    if search:
        heads = heads.filter(
            models.Q(Name__icontains=search) |
            models.Q(Surname__icontains=search) |
            models.Q(MobileNo__icontains=search) |
            models.Q(State__icontains=search) |
            models.Q(City__icontains=search) |
            models.Q(Address__icontains=search)
        )

    # Create a new workbook and select the active worksheet.
    wb = Workbook()
    ws = wb.active
    ws.title = "Heads & Family Members"

    # Define and append the header row.
    headers = [
        "Head Name", "Head Surname", "Mobile", "State", "City", "Address",
        "Member Name", "Member Surname", "Member Mobile", "Relationship",
        "Member Gender", "Member Birthdate", "Member Marital Status"
    ]
    ws.append(headers)

    # Apply bold font to the header row.
    bold_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = bold_font

   
    for head in heads:
        
        state_name = head.State
        city_name = head.City
        
        try:
            state_obj = State.objects.filter(name=head.State).first() or State.objects.filter(id=head.State).first()
            if state_obj:
                state_name = state_obj.name
        except (ValueError, TypeError):
            pass
        
        try:
            city_obj = City.objects.filter(name=head.City).first() or City.objects.filter(id=head.City).first()
            if city_obj:
                city_name = city_obj.name
        except (ValueError, TypeError):
            pass

        # Fetch all family members related to the current head (no member filtering)
        members = head.familymember_set.all()

        # If members exist, add a row for each one.
        if members:
            for member in members:
                ws.append([
                    head.Name, head.Surname, head.MobileNo, state_name, city_name, head.Address,
                    member.Name, member.Surname, member.MobileNo, member.Relationship,
                    member.Gender, member.Birthdate, member.MaritalStatus
                ])
        else:
            # If no members, add a row with just the head's information.
            ws.append([
                head.Name, head.Surname, head.MobileNo, state_name, city_name, head.Address,
                '', '', '', '', '', '', ''
            ])

    # Adjust column widths for better readability.
    for col in ws.columns:
        max_length = 20
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max_length

    # Save the workbook to a byte stream and prepare the response.
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = "heads_family_export.xlsx"
    return FileResponse(output, as_attachment=True, filename=filename)


@require_GET
def check_city_name_unique(request):
    name = request.GET.get('name')
    state_id = request.GET.get('state_id')
    city_id = request.GET.get('city_id')
    qs = City.objects.filter(name__iexact=name, state_id=state_id)
    if city_id:
        qs = qs.exclude(id=city_id)
    exists = qs.exists()
    return JsonResponse({'exists': exists})


@require_GET
def check_state_name_unique(request):
    name = request.GET.get('name')
    country_id = request.GET.get('country_id', 101)
    state_id = request.GET.get('state_id')
    qs = State.objects.filter(name__iexact=name, country_id=country_id)
    if state_id:
        qs = qs.exclude(id=state_id)
    exists = qs.exists()
    return JsonResponse({'exists': exists})

# AJAX endpoint to check if FamilyHead mobile number is unique
@require_GET
def check_head_mobile_unique(request):
    mobile = request.GET.get('mobile')
    head_id = request.GET.get('head_id')  
    qs = FamilyHead.objects.filter(MobileNo=mobile)
    if head_id:
        qs = qs.exclude(HeadID=head_id)
    exists = qs.exists()
    return JsonResponse({'exists': exists})

@login_required(login_url='login')
def pdf_view(request):
    from .models import FamilyHead, FamilyMember, Hobby
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter
    import os

    head_id = request.GET.get('id')
    if head_id:
        from .utils import decode_id
        head_id = decode_id(head_id)
    buffer = io.BytesIO()
    pdf_filename = "family_report.pdf"
    if not head_id:
        c = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(60, 60, "No family selected. Please provide a valid family head ID.")
        c.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=pdf_filename)

    try:
        head = FamilyHead.objects.get(HeadID=head_id)
        members = FamilyMember.objects.filter(HeadID=head)
        pdf_filename = f"family_report_{head.Name}_{head.Surname}_{head_id}.pdf"
    except FamilyHead.DoesNotExist:
        c = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(60, 60, "Family head not found.")
        c.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=pdf_filename)

    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    # Head Photo
    if head.Photo and hasattr(head.Photo, 'path') and os.path.exists(head.Photo.path):
        try:
            img = Image(head.Photo.path, width=120, height=150)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 12))
        except Exception:
            pass

    # Get state and city names if possible
    state_name = head.State
    city_name = head.City
    try:
        state_obj = State.objects.filter(name=head.State).first() or State.objects.filter(id=head.State).first()
        if state_obj:
            state_name = state_obj.name
    except Exception:
        pass
    try:
        city_obj = City.objects.filter(name=head.City).first() or City.objects.filter(id=head.City).first()
        if city_obj:
            city_name = city_obj.name
    except Exception:
        pass

    head_data = [
        [Paragraph('<b>Name</b>', styles['Normal']), f"{head.Name or '-'} {head.Surname or '-'}"],
        [Paragraph('<b>Birthdate</b>', styles['Normal']), str(head.Birthdate) if head.Birthdate else '-'],
        [Paragraph('<b>Gender</b>', styles['Normal']), head.Gender or '-'],
        [Paragraph('<b>Mobile</b>', styles['Normal']), head.MobileNo or '-'],
        [Paragraph('<b>Address</b>', styles['Normal']), head.Address or '-'],
        [Paragraph('<b>State</b>', styles['Normal']), state_name or '-'],
        [Paragraph('<b>City</b>', styles['Normal']), city_name or '-'],
        [Paragraph('<b>Pincode</b>', styles['Normal']), head.Pincode or '-'],
        [Paragraph('<b>Education</b>', styles['Normal']), head.Education or '-'],
        [Paragraph('<b>Marital Status</b>', styles['Normal']), head.MaritalStatus or '-'],
        [Paragraph('<b>Wedding Date</b>', styles['Normal']), str(head.WeddingDate) if head.WeddingDate else 'Not Married'],
        [Paragraph('<b>Hobbies</b>', styles['Normal']), ', '.join([h.Hobby for h in head.head_hobbies.all()]) if head.head_hobbies.exists() else 'None'],
    ]
    head_table = Table(head_data, colWidths=[120, 300])
    head_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1f2a38')),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#1f2a38')),
    ]))
    elements.append(head_table)
    elements.append(Spacer(1, 24))

    # Family Members Table
    member_data = [
        [Paragraph('<b>Photo</b>', styles['Normal']), Paragraph('<b>Name</b>', styles['Normal']), Paragraph('<b>Birthdate</b>', styles['Normal']),
         Paragraph('<b>Gender</b>', styles['Normal']), Paragraph('<b>Mobile</b>', styles['Normal']), Paragraph('<b>Education</b>', styles['Normal']),
         Paragraph('<b>Marital Status</b>', styles['Normal']), Paragraph('<b>Wedding Status</b>', styles['Normal'])]
    ]
    for idx, member in enumerate(members):
        
        photo_cell = '-'
        if member.Photo and hasattr(member.Photo, 'path') and os.path.exists(member.Photo.path):
            try:
                mimg = Image(member.Photo.path, width=40, height=50)
                photo_cell = mimg
            except Exception:
                photo_cell = '-'

        wedding_status = 'Married' if getattr(member, 'MaritalStatus', None) == 'Married' else 'Not Married'
        member_data.append([
            photo_cell,
            f"{member.Name or '-'} {member.Surname or '-'}",
            str(member.Birthdate) if member.Birthdate else '-',
            member.Gender or '-',
            member.MobileNo or '-',
            '-',  
            member.MaritalStatus or '-',
            wedding_status,
        ])

    member_table = Table(member_data, colWidths=[50, 90, 70, 60, 80, 80, 70, 80])
    
    row_colors = [colors.white, colors.HexColor('#f8fafc')]
    table_style = [
        ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor('#1f2a38')),
        ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#1f2a38')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for i in range(1, len(member_data)):
        table_style.append(('BACKGROUND', (0, i), (-1, i), row_colors[i % 2]))
    member_table.setStyle(TableStyle(table_style))
    elements.append(Paragraph('Family Members', styles['Heading2']))
    elements.append(member_table)

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=pdf_filename)

@login_required(login_url='login')
def view_state(request, hashid):
    id = decode_id(hashid)
    from .models import State, City
    state = get_object_or_404(State, id=id)
    search = request.GET.get('search', '').strip()
    cities = state.cities.exclude(status=9)
    if search:
        cities = cities.filter(name__icontains=search)
    return render(request, 'view_state.html', {'state': state, 'cities': cities})

@login_required(login_url='login')
def view_family(request, hashid):
    id = decode_id(hashid)
    head = get_object_or_404(FamilyHead, HeadID=id)
    members = head.familymember_set.all()
    
    state_name = head.State
    city_name = head.City
    try:
        state_obj = State.objects.filter(name=head.State).first() or State.objects.filter(id=head.State).first()
        if state_obj:
            state_name = state_obj.name
    except Exception:
        pass
    try:
        city_obj = City.objects.filter(name=head.City).first() or City.objects.filter(id=head.City).first()
        if city_obj:
            city_name = city_obj.name
    except Exception:
        pass
    return render(request, 'view_family.html', {'head': head, 'members': members, 'state_name': state_name, 'city_name': city_name})

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def add_state(request):
    error = None
    if request.method == "POST":
        name = request.POST.get("name")
        country_id = request.POST.get("country_id") or 101
        if not name:
            error = "State name is required."
        elif State.objects.filter(name__iexact=name, country_id=country_id).exists():
            error = "State with this name already exists."
        else:
            last_state = State.objects.order_by('-id').first()
            next_id = (last_state.id + 1) if last_state else 1
            from .models import Country
            india = Country.objects.get(id=101)
            state = State(id=next_id, name=name, status=1, country=india)
            try:
                state.save()
                messages.success(request, 'State added successfully!')
                return redirect('dashboard')
            except Exception as e:
                error = str(e)
    return render(request, 'add_state.html', {'error': error})

from django.views.decorators.http import require_http_methods

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def add_city(request):
    error = None
    states = State.objects.filter(country_id=101)
    if request.method == "POST":
        state_id = request.POST.get("state_id")
        city_name = request.POST.get("name")
        if not state_id or not city_name:
            error = "State and city name are required."
        elif City.objects.filter(name__iexact=city_name, state_id=state_id).exists():
            error = "City with this name already exists in the selected state."
        else:
            try:
                state = State.objects.get(id=state_id)
                last_city = City.objects.order_by('-id').first()
                next_id = (last_city.id + 1) if last_city else 1
                city = City(id=next_id, name=city_name, state=state, country_id=state.country.id, status=1)
                city.save()
                messages.success(request, 'City added successfully!')
                return redirect('dashboard')
            except Exception as e:
                error = str(e)
    
    
    return render(request, 'add_city.html', {'states': states, 'error': error})



##__________Without validation code_______

# def update_head(request, id):
#     instance = get_object_or_404(FamilyHead, HeadID=id)
#     if request.method == 'POST':
#         instance.Name = request.POST.get('head_name')
#         instance.Surname = request.POST.get('head_surname')
#         instance.Gender = request.POST.get('head_gender')
#         instance.Birthdate = request.POST.get('head_birthdate')
#         instance.MobileNo = request.POST.get('head_mobile')
#         instance.Address = request.POST.get('head_address')
#         instance.State = request.POST.get('head_state')
#         instance.City = request.POST.get('head_city')
#         instance.Pincode = request.POST.get('head_pincode')
#         instance.MaritalStatus = request.POST.get('head_marital_status')
#         instance.WeddingDate = request.POST.get('head_wedding_date') or None
#         instance.Education = request.POST.get('head_education')
#         if request.FILES.get('head_photo'):
#             instance.Photo = request.FILES.get('head_photo')
#         instance.save()

#         # Log update action for FamilyHead
#         if request.user.is_authenticated:
#             AdminLog.objects.create(
#                 user=request.user,
#                 username=request.user.username,
#                 action='update',
#                 description=f'Updated FamilyHead: {instance.Name} {instance.Surname}',
#                 object_id=str(instance.HeadID),
#                 object_type='FamilyHead'
#             )

#         # family members
#         members = FamilyMember.objects.filter(HeadID=instance)
#         for idx, member in enumerate(members, start=1):
#             member.Name = request.POST.get(f'member_{idx}_name')
#             member.Surname = request.POST.get(f'member_{idx}_surname')
#             member.Birthdate = request.POST.get(f'member_{idx}_birthdate')
#             member.MobileNo = request.POST.get(f'member_{idx}_mobile')
#             member.Gender = request.POST.get(f'member_{idx}_gender')
#             member.Relationship = request.POST.get(f'member_{idx}_relationship')
#             member.Education = request.POST.get(f'member_{idx}_education')
#             member.MaritalStatus = request.POST.get(f'member_{idx}_marital_status')
#             member.WeddingDate = request.POST.get(f'member_{idx}_wedding_date') or None
#             if request.FILES.get(f'member_{idx}_photo'):
#                 member.Photo = request.FILES.get(f'member_{idx}_photo')
#             member.save()
#             # Log update action for FamilyMember
#             if request.user.is_authenticated:
#                 AdminLog.objects.create(
#                     user=request.user,
#                     username=request.user.username,
#                     action='update',
#                     description=f'Updated FamilyMember: {member.Name} {member.Surname}',
#                     object_id=str(member.MemberID),
#                     object_type='FamilyMember'
#                 )

#         # Add new members if present in POST data
#         existing_count = members.count()
#         new_idx = existing_count + 1
#         while request.POST.get(f'member_{new_idx}_name'):
#             new_member = FamilyMember(
#                 HeadID=instance,
#                 Name=request.POST.get(f'member_{new_idx}_name'),
#                 Surname=request.POST.get(f'member_{new_idx}_surname'),
#                 Birthdate=request.POST.get(f'member_{new_idx}_birthdate'),
#                 MobileNo=request.POST.get(f'member_{new_idx}_mobile'),
#                 Gender=request.POST.get(f'member_{new_idx}_gender'),
#                 Relationship=request.POST.get(f'member_{new_idx}_relationship'),
#                 Education=request.POST.get(f'member_{new_idx}_education'),
#                 MaritalStatus=request.POST.get(f'member_{new_idx}_marital_status'),
#                 WeddingDate=request.POST.get(f'member_{new_idx}_wedding_date') or None,
#             )
#             if request.FILES.get(f'member_{new_idx}_photo'):
#                 new_member.Photo = request.FILES.get(f'member_{new_idx}_photo')
#             new_member.save()
#             # Log create action for new FamilyMember
#             if request.user.is_authenticated:
#                 AdminLog.objects.create(
#                     user=request.user,
#                     username=request.user.username,
#                     action='create',
#                     description=f'Created FamilyMember: {new_member.Name} {new_member.Surname}',
#                     object_id=str(new_member.MemberID),
#                     object_type='FamilyMember'
#                 )
#             new_idx += 1

#         messages.success(request, 'Head and family updated successfully!')
#         return redirect('dashboard')
#     # GET request: show edit form
#     states = list(State.objects.filter(country_id=101).values('id', 'name'))
#     members = FamilyMember.objects.filter(HeadID=instance)
#     return render(request, 'edit_registration.html', {'head': instance, 'states': states, 'members': members})


@login_required(login_url='login')
def update_head(request, hashid):
    id = decode_id(hashid)
    instance = get_object_or_404(FamilyHead, HeadID=id)
    states = list(State.objects.filter(country_id=101).values('id', 'name'))
    
    if request.method == 'POST':
        error_messages = []
        
        # --- Head Validation ---
        head_name = request.POST.get('head_name', '').strip()
        if not head_name:
            error_messages.append('*First name is required for Family Head.')
        
        head_surname = request.POST.get('head_surname', '').strip()
        if not head_surname:
            error_messages.append('*Surname is required for Family Head.')
            
        head_mobile = request.POST.get('head_mobile', '').strip()
        if not head_mobile or not head_mobile.isdigit() or len(head_mobile) != 10:
            error_messages.append('*A valid 10-digit mobile number is required for Family Head.')
        
        if head_mobile and FamilyHead.objects.filter(MobileNo=head_mobile).exclude(HeadID=instance.HeadID).exists():
            error_messages.append('*This mobile number is already registered. Please use a different number.')

        head_address = request.POST.get('head_address', '').strip()
        if not head_address:
            error_messages.append('*Address is required for Family Head.')

        head_state_id = request.POST.get('head_state', '').strip()
        if not head_state_id:
            error_messages.append('*State is required for Family Head.')

        head_city = request.POST.get('head_city', '').strip()
        if not head_city:
            error_messages.append('*City is required for Family Head.')

        head_pincode = request.POST.get('head_pincode', '').strip()
        if not head_pincode or not head_pincode.isdigit() or len(head_pincode) != 6:
            error_messages.append('*A valid 6-digit pincode is required for Family Head.')

        head_gender = request.POST.get('head_gender', '').strip()
        if not head_gender:
            error_messages.append('*Gender is required for Family Head.')

        head_marital_status = request.POST.get('head_marital_status', '').strip()
        if not head_marital_status:
            error_messages.append('*Marital Status is required for Family Head.')
        elif head_marital_status == 'Married':
            head_wedding_date = request.POST.get('head_wedding_date', '').strip()
            if not head_wedding_date:
                error_messages.append('Wedding date is required for a married Family Head.')

        head_birthdate_str = request.POST.get('head_birthdate', '').strip()
        if not head_birthdate_str:
            error_messages.append('*Birthdate is required for Family Head.')
        else:
            try:
                head_birthdate = datetime.datetime.strptime(head_birthdate_str, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - head_birthdate.year - ((today.month, today.day) < (head_birthdate.month, head_birthdate.day))
                if age < 21:
                    error_messages.append('*Family Head must be 21 years or older.')
            except ValueError:
                error_messages.append('*Invalid birthdate format for Family Head.')

        head_education = request.POST.get('head_education', '').strip()
        if not head_education:
            error_messages.append('*Education is required for Family Head.')
        
        head_photo = request.FILES.get('head_photo')
        
        if not head_photo and not instance.Photo:
            error_messages.append('Photo is required for Family Head.')
        elif head_photo:
            if head_photo.size > 2 * 1024 * 1024:
                error_messages.append('Family Head photo size must be less than 2MB.')
            if head_photo.content_type not in ['image/jpeg', 'image/png']:
                error_messages.append('Family Head photo must be a JPG or PNG file.')

        head_hobbies = request.POST.getlist('head_hobbies[]')
        if not any(hobby.strip() for hobby in head_hobbies):
            error_messages.append('At least one hobby is required for Family Head.')

        
        members = FamilyMember.objects.filter(HeadID=instance)
        for idx, member in enumerate(members, start=1):
            member_name = request.POST.get(f'member_{idx}_name', '').strip()
            if not member_name:
                error_messages.append(f'First name is required for member {idx}.')
            
            member_surname = request.POST.get(f'member_{idx}_surname', '').strip()
            if not member_surname:
                error_messages.append(f'Surname is required for member {idx}.')

            member_relationship = request.POST.get(f'member_{idx}_relationship', '').strip()
            if not member_relationship:
                error_messages.append(f'Relationship is required for member {idx}.')

            member_birthdate_str = request.POST.get(f'member_{idx}_birthdate', '').strip()
            if not member_birthdate_str:
                error_messages.append(f'Birthdate is required for member {idx}.')

            member_marital_status = request.POST.get(f'member_{idx}_marital_status', '').strip()
            if not member_marital_status:
                error_messages.append(f'Marital Status is required for member {idx}.')
            elif member_marital_status == 'Married':
                member_wedding_date = request.POST.get(f'member_{idx}_wedding_date', '').strip()
                if not member_wedding_date:
                    error_messages.append(f'Wedding date is required for a married member {idx}.')

            member_gender = request.POST.get(f'member_{idx}_gender', '').strip()
            if not member_gender:
                error_messages.append(f'Gender is required for member {idx}.')

            member_education = request.POST.get(f'member_{idx}_education', '').strip()
            if not member_education:
                error_messages.append(f'Education is required for member {idx}.')
            
            member_photo = request.FILES.get(f'member_{idx}_photo')
            if not member_photo and not member.Photo:
                error_messages.append(f'Photo is required for member {idx}.')
            elif member_photo:
                if member_photo.size > 2 * 1024 * 1024:
                    error_messages.append(f'Member {idx} photo size must be less than 2MB.')
                if member_photo.content_type not in ['image/jpeg', 'image/png']:
                    error_messages.append(f'Member {idx} photo must be a JPG or PNG file.')


        new_idx = members.count() + 1
        while request.POST.get(f'member_{new_idx}_name'):
            member_name = request.POST.get(f'member_{new_idx}_name', '').strip()
            if not member_name:
                error_messages.append(f'First name is required for new member {new_idx}.')
            
            member_surname = request.POST.get(f'member_{new_idx}_surname', '').strip()
            if not member_surname:
                error_messages.append(f'Surname is required for new member {new_idx}.')

            member_relationship = request.POST.get(f'member_{new_idx}_relationship', '').strip()
            if not member_relationship:
                error_messages.append(f'Relationship is required for new member {new_idx}.')

            member_birthdate_str = request.POST.get(f'member_{new_idx}_birthdate', '').strip()
            if not member_birthdate_str:
                error_messages.append(f'Birthdate is required for new member {new_idx}.')

            member_marital_status = request.POST.get(f'member_{new_idx}_marital_status', '').strip()
            if not member_marital_status:
                error_messages.append(f'Marital Status is required for new member {new_idx}.')
            elif member_marital_status == 'Married':
                member_wedding_date = request.POST.get(f'member_{new_idx}_wedding_date', '').strip()
                if not member_wedding_date:
                    error_messages.append(f'Wedding date is required for a married new member {new_idx}.')

            member_gender = request.POST.get(f'member_{new_idx}_gender', '').strip()
            if not member_gender:
                error_messages.append(f'Gender is required for new member {new_idx}.')

            member_education = request.POST.get(f'member_{new_idx}_education', '').strip()
            if not member_education:
                error_messages.append(f'Education is required for new member {new_idx}.')
            
            member_photo = request.FILES.get(f'member_{new_idx}_photo')
            if not member_photo:
                error_messages.append(f'Photo is required for new member {new_idx}.')
            elif member_photo:
                if member_photo.size > 2 * 1024 * 1024:
                    error_messages.append(f'New member {new_idx} photo size must be less than 2MB.')
                if member_photo.content_type not in ['image/jpeg', 'image/png']:
                    error_messages.append(f'New member {new_idx} photo must be a JPG or PNG file.')

            new_idx += 1

        if error_messages:
            return JsonResponse({'success': False, 'errors': error_messages})
        
        # If no validation errors, proceed with the database transaction
        try:
            with transaction.atomic():
                # Update and save Family Head
                instance.Name = head_name
                instance.Surname = head_surname
                instance.Gender = head_gender
                instance.Birthdate = head_birthdate_str
                instance.MobileNo = head_mobile
                instance.Address = head_address
                instance.State = head_state_id
                instance.City = head_city
                instance.Pincode = head_pincode
                instance.MaritalStatus = head_marital_status
                instance.WeddingDate = request.POST.get('head_wedding_date') or None
                instance.Education = head_education
                if request.FILES.get('head_photo'):
                    instance.Photo = request.FILES.get('head_photo')
                instance.save()
                

                if request.user.is_authenticated:
                    AdminLog.objects.create(
                        user=request.user,
                        username=request.user.username,
                        action='update',
                        description=f'Updated FamilyHead: {instance.Name} {instance.Surname}',
                        object_id=str(instance.HeadID),
                        object_type='FamilyHead'
                    )

                Hobby.objects.filter(head=instance).delete()
                for hobby in head_hobbies:
                    if hobby.strip():
                        Hobby.objects.create(head=instance, Hobby=hobby.strip())

                members = FamilyMember.objects.filter(HeadID=instance)
                for idx, member in enumerate(members, start=1):
                    member.Name = request.POST.get(f'member_{idx}_name')
                    member.Surname = request.POST.get(f'member_{idx}_surname')
                    member.Birthdate = request.POST.get(f'member_{idx}_birthdate') or None
                    member.MobileNo = request.POST.get(f'member_{idx}_mobile')
                    member.Gender = request.POST.get(f'member_{idx}_gender')
                    member.Relationship = request.POST.get(f'member_{idx}_relationship')
                    member.Education = request.POST.get(f'member_{idx}_education')
                    member.MaritalStatus = request.POST.get(f'member_{idx}_marital_status')
                    member.WeddingDate = request.POST.get(f'member_{idx}_wedding_date') or None
                    if request.FILES.get(f'member_{idx}_photo'):
                        member.Photo = request.FILES.get(f'member_{idx}_photo')
                    member.save()
                    
                    if request.user.is_authenticated:
                        AdminLog.objects.create(
                            user=request.user,
                            username=request.user.username,
                            action='update',
                            description=f'Updated FamilyMember: {member.Name} {member.Surname}',
                            object_id=str(member.MemberID),
                            object_type='FamilyMember'
                        )

                # Add new members
                new_idx = members.count() + 1
                while request.POST.get(f'member_{new_idx}_name'):
                    new_member = FamilyMember(
                        HeadID=instance,
                        Name=request.POST.get(f'member_{new_idx}_name'),
                        Surname=request.POST.get(f'member_{new_idx}_surname'),
                        Birthdate=request.POST.get(f'member_{new_idx}_birthdate') or None,
                        MobileNo=request.POST.get(f'member_{new_idx}_mobile'),
                        Gender=request.POST.get(f'member_{new_idx}_gender'),
                        Relationship=request.POST.get(f'member_{new_idx}_relationship'),
                        Education=request.POST.get(f'member_{new_idx}_education'),
                        MaritalStatus=request.POST.get(f'member_{new_idx}_marital_status'),
                        WeddingDate=request.POST.get(f'member_{new_idx}_wedding_date') or None,
                    )
                    if request.FILES.get(f'member_{new_idx}_photo'):
                        new_member.Photo = request.FILES.get(f'member_{new_idx}_photo')
                    new_member.save()
                    
                    if request.user.is_authenticated:
                        AdminLog.objects.create(
                            user=request.user,
                            username=request.user.username,
                            action='create',
                            description=f'Created FamilyMember: {new_member.Name} {new_member.Surname}',
                            object_id=str(new_member.MemberID),
                            object_type='FamilyMember'
                        )
                    new_idx += 1

                return JsonResponse({'success': True, 'message': 'Family updated successfully!'})
    
        
        except IntegrityError:
            return JsonResponse({'success': False, 'errors': ['A database error occurred. Please try again later.']})

    return render(request, 'edit_registration.html', {'head': instance, 'states': states, 'members': FamilyMember.objects.filter(HeadID=instance)})


@login_required(login_url='login')
def edit_state(request, hashid):
    id = decode_id(hashid)
    state = get_object_or_404(State, id=id)
    if request.method == 'POST':
        new_name = request.POST.get('name')
        if State.objects.filter(name__iexact=new_name, country=state.country).exclude(id=state.id).exists():
            messages.error(request, 'State with this name already exists.')
            return render(request, 'edit_state.html', {'state': state})
        state.name = new_name
        state.save()
        # Log update action for State
        if request.user.is_authenticated:
            AdminLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='update',
                description=f'Updated State: {state.name}',
                object_id=str(state.id),
                object_type='State'
            )
        messages.success(request, 'State updated successfully!')
        return redirect('dashboard_state')
    return render(request, 'edit_state.html', {'state': state})


@login_required(login_url='login')
def edit_city(request, hashid):
    id = decode_id(hashid)
    city = get_object_or_404(City, id=id)
    if request.method == 'POST':
        city.name = request.POST.get('name')
        city.save()

        if request.user.is_authenticated:
            AdminLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='update',
                description=f'Updated City: {city.name}',
                object_id=str(city.id),
                object_type='City'
            )
        messages.success(request, 'City updated successfully!')
        return redirect('dashboard_city')
    return render(request, 'edit_city.html', {'city': city})

@login_required(login_url='login')
@csrf_exempt
def update_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entry_type = data.get('type')
        entry_id = data.get('id')
        status = data.get('status')
        try:
            import os
            if entry_type == 'head':
                obj = FamilyHead.objects.get(HeadID=entry_id)
                obj.status = status
                obj.save()
                if status == 9:
                    
                    if obj.Photo and hasattr(obj.Photo, 'path') and os.path.exists(obj.Photo.path):
                        try:
                            os.remove(obj.Photo.path)
                        except Exception:
                            pass
                    obj.Photo = None
                    obj.save()
                   
                    for member in FamilyMember.objects.filter(HeadID=obj):
                        member.status = 9
                        if member.Photo and hasattr(member.Photo, 'path') and os.path.exists(member.Photo.path):
                            try:
                                os.remove(member.Photo.path)
                            except Exception:
                                pass
                        member.Photo = None
                        member.save()
            elif entry_type == 'member':
                obj = FamilyMember.objects.get(MemberID=entry_id)
                obj.status = status
                obj.save()
                if status == 9:
                    if obj.Photo and hasattr(obj.Photo, 'path') and os.path.exists(obj.Photo.path):
                        try:
                            os.remove(obj.Photo.path)
                        except Exception:
                            pass
                    obj.Photo = None
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
    inactive_members = FamilyMember.objects.exclude(status=9).filter(status=0).count() + FamilyHead.objects.exclude(status=9).filter(status=0).count()
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
        'inactive_members': inactive_members,
        'total_cities': total_cities,
        'labels': labels,
        'data': data,
    }
    return render(request, 'stats.html', context)

# AJAX dashboard card
from django.views.decorators.http import require_GET
@require_GET
def dashboard_stats_api(request):
    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.exclude(status=9).filter(status=1).count() + FamilyHead.objects.exclude(status=9).filter(status=1).count()
    inactive_members = FamilyMember.objects.exclude(status=9).filter(status=0).count() + FamilyHead.objects.exclude(status=9).filter(status=0).count()
    return JsonResponse({
        'total_families': total_families,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
    })

def home(request):
    return render(request, 'home_copy.html')


# def regis(request):
#     states = list(State.objects.filter(country_id=101).values('id', 'name'))

#     if request.method == 'POST':
#         error_messages = []
#         # Validate head gender
#         head_gender = request.POST.get('head_gender')
#         # if not head_gender:
#         #     error_messages.append('Gender is required for Family Head.')
#         # Validate other required head fields (optional: add more as needed)
#         # Validate members gender
#         member_index = 1
#         while True:
#             name = request.POST.get(f'member_{member_index}_name')
#             if not name:
#                 break
#             member_gender = request.POST.get(f'member_{member_index}_gender')
#             if not member_gender:
#                 error_messages.append(f'Gender is required for member {member_index}.')
#             member_index += 1

#         if error_messages:
#             for msg in error_messages:
#                 messages.error(request, msg)
#             return render(request, 'registration.html', {'states': states})

#         # Family Head - check unique mobile
#         head_mobile = request.POST.get('head_mobile')
#         if FamilyHead.objects.filter(MobileNo=head_mobile).exists():
#             messages.error(request, 'This mobile number is already registered. Please use a different number.')
#             return render(request, 'registration.html', {'states': states})
#         head_birthdate = request.POST.get('head_birthdate')
#         if head_birthdate == '':
#             head_birthdate = None
#         head = FamilyHead(
#             Name=request.POST.get('head_name'),
#             Surname=request.POST.get('head_surname'),
#             Gender =head_gender,
#             Birthdate=head_birthdate,
#             MobileNo=head_mobile,
#             Address=request.POST.get('head_address'),
#             State=request.POST.get('head_state'),
#             City=request.POST.get('head_city'),
#             Pincode=request.POST.get('head_pincode'),
#             MaritalStatus=request.POST.get('head_marital_status'),
#             WeddingDate=request.POST.get('head_wedding_date') or None,
#             Education=request.POST.get('head_education'),
#             Photo=request.FILES.get('head_photo')
#         )
#         head.save()

#         # Log create action for FamilyHead
#         if request.user.is_authenticated:
#             AdminLog.objects.create(
#                 user=request.user,
#                 username=request.user.username,
#                 action='create',
#                 description=f'Created FamilyHead: {head.Name} {head.Surname}',
#                 object_id=str(head.HeadID),
#                 object_type='FamilyHead'
#             )

#         # Hobbies for Head
#         for hobby in request.POST.getlist('head_hobbies[]'):
#             if hobby.strip():
#                 Hobby.objects.create(head=head, Hobby=hobby.strip())

#         # Family Members
#         member_index = 1
#         while True:
#             name = request.POST.get(f'member_{member_index}_name')
#             if not name:
#                 break
#             address = request.POST.get(f'member_{member_index}_address')
#             address_override = bool(address)
#             if not address_override:
#                 # Inherit address from head
#                 address = head.Address
#                 state = head.State
#                 city = head.City
#                 pincode = head.Pincode
#             else:
#                 state = request.POST.get(f'member_{member_index}_state')
#                 city = request.POST.get(f'member_{member_index}_city')
#                 pincode = request.POST.get(f'member_{member_index}_pincode')
#             member_birthdate = request.POST.get(f'member_{member_index}_birthdate')
#             if member_birthdate == '':
#                 member_birthdate = None
#             member_gender = request.POST.get(f'member_{member_index}_gender')
#             member = FamilyMember(
#                 HeadID=head,
#                 Name=name,
#                 Surname=request.POST.get(f'member_{member_index}_surname'),
#                 Gender=member_gender,
#                 Relationship=request.POST.get(f'member_{member_index}_relationship'),
#                 Birthdate=member_birthdate,
#                 MobileNo=request.POST.get(f'member_{member_index}_mobile'),
#                 Photo=request.FILES.get(f'member_{member_index}_photo'),
#                 MaritalStatus=request.POST.get(f'member_{member_index}_marital_status'),
#             )
#             member.save()
#             # Log create action for FamilyMember
#             if request.user.is_authenticated:
#                 AdminLog.objects.create(
#                     user=request.user,
#                     username=request.user.username,
#                     action='create',
#                     description=f'Created FamilyMember: {member.Name} {member.Surname}',
#                     object_id=str(member.MemberID),
#                     object_type='FamilyMember'
#                 )
#             # Member hobbies
#             for hobby in request.POST.getlist(f'member_{member_index}_hobbies[]'):
#                 if hobby.strip():
#                     Hobby.objects.create(head=head, member=member, Hobby=hobby.strip())
#             member_index += 1

#         messages.success(request, 'Family registered successfully!')
#         return redirect('regis')

#     return render(request, 'registration.html', {'states': states})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            # Log login action
            AdminLog.objects.create(
                user=user,
                username=user.username,
                action='login',
                description='Admin logged in',
                object_id=str(user.id),
                object_type='User'
            )
            messages.success(request, 'Login successful!')
            return redirect('dashboard_head')
        else:
            # Pass error_message for client-side display
            return render(request, 'login.html', {'error_message': 'Invalid credentials or not a superuser', 'username': username})

    return render(request, 'login.html')



def regis(request):
    states = list(State.objects.filter(country_id=101).values('id', 'name'))
    
    search = request.GET.get('search')
    show_all_tables = bool(search)
    
    heads = FamilyHead.objects.all()
    families = FamilyMember.objects.all()

    if search:
        heads = heads.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(State__icontains=search) |
            Q(City__icontains=search) |
            Q(Address__icontains=search)
        )
        families = families.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(Relationship__icontains=search)
        )
        
    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + total_families
    active_members = FamilyMember.objects.filter(status=1).exclude(status=9).count() + FamilyHead.objects.filter(status=1).exclude(status=9).count()
    inactive_members = FamilyMember.objects.filter(status=0).exclude(status=9).count() + FamilyHead.objects.filter(status=0).exclude(status=9).count()
    deleted = FamilyMember.objects.filter(status=9).count() + FamilyHead.objects.filter(status=9).count()

    if request.method == 'POST':
        error_messages = []
        
        # --- Head Validation ---
        head_name = request.POST.get('head_name', '').strip()
        if not head_name:
            error_messages.append('First name is required for Family Head.')
        
        head_surname = request.POST.get('head_surname', '').strip()
        if not head_surname:
            error_messages.append('Surname is required for Family Head.')
        
        head_mobile = request.POST.get('head_mobile', '').strip()
        if not head_mobile or not head_mobile.isdigit() or len(head_mobile) != 10:
            error_messages.append('A valid 10-digit mobile number is required for Family Head.')
        
        head_address = request.POST.get('head_address', '').strip()
        if not head_address:
            error_messages.append('Address is required for Family Head.')
            
        head_state_id = request.POST.get('head_state', '').strip()
        if not head_state_id:
            error_messages.append('State is required for Family Head.')

        head_city = request.POST.get('head_city', '').strip()
        if not head_city:
            error_messages.append('City is required for Family Head.')
            
        head_pincode = request.POST.get('head_pincode', '').strip()
        if not head_pincode or not head_pincode.isdigit() or len(head_pincode) != 6:
            error_messages.append('A valid 6-digit pincode is required for Family Head.')

        head_gender = request.POST.get('head_gender', '').strip()
        if not head_gender:
            error_messages.append('Gender is required for Family Head.')
            
        head_marital_status = request.POST.get('head_marital_status', '').strip()
        if not head_marital_status:
            error_messages.append('Marital Status is required for Family Head.')
        elif head_marital_status == 'Married' and not request.POST.get('head_wedding_date'):
            error_messages.append('Wedding date is required for a married Family Head.')
        
        head_birthdate = request.POST.get('head_birthdate', '').strip()
        if not head_birthdate:
            error_messages.append('Birthdate is required for Family Head.')
        else:
            try:
                birth_date_obj = datetime.datetime.strptime(head_birthdate, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))
                if age < 21:
                    error_messages.append('Family Head must be 21 years or older.')
            except ValueError:
                error_messages.append('Invalid birthdate format for Family Head.')
        
        head_education = request.POST.get('head_education', '').strip()
        if not head_education:
            error_messages.append('Education is required for Family Head.')
        
        head_photo = request.FILES.get('head_photo')
        if not head_photo:
            error_messages.append('Photo is required for Family Head.')
        
        head_hobbies = request.POST.getlist('head_hobbies[]')
        if not any(hobby.strip() for hobby in head_hobbies):
            error_messages.append('At least one hobby is required for Family Head.')

        # Family Head - check unique mobile
        if FamilyHead.objects.filter(MobileNo=head_mobile).exists():
            error_messages.append('This mobile number is already registered.')
        
        # --- Member Validation ---
        member_index = 1
        while True:
            name = request.POST.get(f'member_{member_index}_name')
            if not name:
                break
            
            member_surname = request.POST.get(f'member_{member_index}_surname', '')
            if not member_surname:
                error_messages.append(f'Surname is required for member {member_index}.')
            
            member_gender = request.POST.get(f'member_{member_index}_gender', '')
            if not member_gender:
                error_messages.append(f'Gender is required for member {member_index}.')
            
            member_relationship = request.POST.get(f'member_{member_index}_relationship', '')
            if not member_relationship:
                error_messages.append(f'Relationship is required for member {member_index}.')
            
            member_birthdate = request.POST.get(f'member_{member_index}_birthdate', '')
            if not member_birthdate:
                error_messages.append(f'Birthdate is required for member {member_index}.')
            
            member_marital_status = request.POST.get(f'member_{member_index}_marital_status', '')
            if not member_marital_status:
                error_messages.append(f'Marital Status is required for member {member_index}.')
            elif member_marital_status == 'Married' and not request.POST.get(f'member_{member_index}_wedding_date'):
                error_messages.append(f'Wedding date is required for a married member {member_index}.')
            
            member_photo = request.FILES.get(f'member_{member_index}_photo')
            if not member_photo:
                error_messages.append(f'Photo is required for member {member_index}.')
            
            member_index += 1
        
        if error_messages:
            return JsonResponse({'success': False, 'errors': error_messages})
        
        # Data is valid, now convert and save
        try:
            head_state = get_object_or_404(State, id=head_state_id)
            head_birthdate_obj = None
            if head_birthdate:
                head_birthdate_obj = datetime.datetime.strptime(head_birthdate, '%Y-%m-%d').date()
            
            head_wedding_date_obj = None
            if head_marital_status == 'Married':
                head_wedding_date_str = request.POST.get('head_wedding_date')
                if head_wedding_date_str:
                    head_wedding_date_obj = datetime.datetime.strptime(head_wedding_date_str, '%Y-%m-%d').date()

            with transaction.atomic():
                # Create and save Family Head
                head = FamilyHead(
                    Name=head_name,
                    Surname=head_surname,
                    Gender=head_gender,
                    Birthdate=head_birthdate_obj,
                    MobileNo=head_mobile,
                    Address=head_address,
                    State=head_state.name, # Save the state name, not the ID
                    City=head_city,
                    Pincode=head_pincode,
                    MaritalStatus=head_marital_status,
                    WeddingDate=head_wedding_date_obj,
                    Education=head_education,
                    Photo=head_photo
                )
                head.save()
                
                if request.user.is_authenticated:
                    AdminLog.objects.create(
                        user=request.user,
                        username=request.user.username,
                        action='create',
                        description=f'Created FamilyHead: {head.Name} {head.Surname}',
                        object_id=str(head.HeadID),
                        object_type='FamilyHead'
                    )
                
                for hobby in head_hobbies:
                    if hobby.strip():
                        Hobby.objects.create(head=head, Hobby=hobby.strip())
                
                member_index = 1
                while True:
                    name = request.POST.get(f'member_{member_index}_name')
                    if not name:
                        break
                    
                    member_birthdate_str = request.POST.get(f'member_{member_index}_birthdate')
                    member_birthdate_obj = None
                    if member_birthdate_str:
                        member_birthdate_obj = datetime.datetime.strptime(member_birthdate_str, '%Y-%m-%d').date()
                    
                    member_marital_status = request.POST.get(f'member_{member_index}_marital_status', '')
                    member_wedding_date_obj = None
                    if member_marital_status == 'Married':
                        member_wedding_date_str = request.POST.get(f'member_{member_index}_wedding_date')
                        if member_wedding_date_str:
                            member_wedding_date_obj = datetime.datetime.strptime(member_wedding_date_str, '%Y-%m-%d').date()

                    member_photo = request.FILES.get(f'member_{member_index}_photo')
                    
                    member = FamilyMember(
                        HeadID=head,
                        Name=name,
                        Surname=request.POST.get(f'member_{member_index}_surname'),
                        Gender=request.POST.get(f'member_{member_index}_gender'),
                        Relationship=request.POST.get(f'member_{member_index}_relationship'),
                        Birthdate=member_birthdate_obj,
                        MobileNo=request.POST.get(f'member_{member_index}_mobile') or None,
                        Photo=member_photo,
                        MaritalStatus=member_marital_status,
                        WeddingDate=member_wedding_date_obj,
                        Education=request.POST.get(f'member_{member_index}_education'),
                    )
                    member.save()
                    
                    if request.user.is_authenticated:
                        AdminLog.objects.create(
                            user=request.user,
                            username=request.user.username,
                            action='create',
                            description=f'Created FamilyMember: {member.Name} {member.Surname}',
                            object_id=str(member.MemberID),
                            object_type='FamilyMember'
                        )
                    member_index += 1
                
                return JsonResponse({'success': True, 'message': 'Family registered successfully!'})
        
        except State.DoesNotExist:
            return JsonResponse({'success': False, 'errors': ['Invalid state selected.']})
        except ValueError as e:
            return JsonResponse({'success': False, 'errors': [f'Data format error: {e}']})
        except IntegrityError as e:
            return JsonResponse({'success': False, 'errors': [f'A database error occurred: {e}']})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'An unexpected server error occurred: {e}']})
    
    return render(request, 'registration.html', {'states': states})


def resetPassword(request):
    return render(request, 'resetPassword.html')

@login_required(login_url='login')
def dashboard_head(request):
    head_page = request.GET.get('head_page', 1)
    family_page = request.GET.get('family_page', 1)
    state_page = request.GET.get('state_page', 1)
    city_page = request.GET.get('city_page', 1)
    search = request.GET.get('search', '').strip()
    state_filter = request.GET.get('state_filter', '')


    heads = FamilyHead.objects.exclude(status=9).order_by('-HeadID')
    families = FamilyMember.objects.exclude(status=9).order_by('-MemberID')
    
    # Assuming State and City also need to be ordered latest first
    states = State.objects.exclude(status=9).order_by('-id') if hasattr(State, 'status') else State.objects.all().order_by('-id')
    all_states = State.objects.exclude(status=9).order_by('name') # Usually, the filter list of states is ordered alphabetically
    # ------------------------------------------------------------------------------------

    if state_filter:
        filtered_cities = City.objects.exclude(status=9).filter(state_id=state_filter).order_by('-id')
    else:
        filtered_cities = City.objects.exclude(status=9).order_by('-id')

    # Enable search filtering
    if search:
        heads = heads.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(State__icontains=search) |
            Q(City__icontains=search) |
            Q(Address__icontains=search)
        )
        families = families.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(Relationship__icontains=search)
        )
        states = states.filter(Q(name__icontains=search))
        filtered_cities = filtered_cities.filter(Q(name__icontains=search))
        show_all_tables = True
    else:
        show_all_tables = False

    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.filter(status=1).exclude(status=9).count() + FamilyHead.objects.filter(status=1).exclude(status=9).count()
    inactive_members = FamilyMember.objects.filter(status=0).exclude(status=9).count() + FamilyHead.objects.filter(status=0).exclude(status=9).count()
    deleted = FamilyMember.objects.filter(status=9).count() + FamilyHead.objects.filter(status=9).count()

    # The line where you had the error is now corrected by ordering the QuerySet beforehand
    head_paginator = Paginator(heads, 10) # 'heads' is already ordered
    family_paginator = Paginator(families, 10)
    state_paginator = Paginator(states, 10)
    city_paginator = Paginator(filtered_cities, 10)

    context = {
        'search': search,
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
        'show_all_tables': show_all_tables,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dashboard_head.html', context, content_type='text/html')
    return render(request, 'dashboard_head.html', context)



@login_required(login_url='login')
def dashboard_family(request):
    search = request.GET.get('search', '').strip()
    state_filter = request.GET.get('state_filter', '')

    heads = FamilyHead.objects.exclude(status=9)
    families = FamilyMember.objects.exclude(status=9)
    states = State.objects.exclude(status=9) if hasattr(State, 'status') else State.objects.all()
    all_states = State.objects.exclude(status=9)
    if state_filter:
        filtered_cities = City.objects.exclude(status=9).filter(state_id=state_filter)
    else:
        filtered_cities = City.objects.exclude(status=9)

    show_all_tables = False
    if search:
        # Correct filtering for each table based on its model's fields
        heads = heads.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(State__icontains=search) |
            Q(City__icontains=search) |
            Q(Address__icontains=search)
        )
        families = families.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(Relationship__icontains=search)
        )
        states = states.filter(
            Q(name__icontains=search)
        )
        filtered_cities = filtered_cities.filter(
            Q(name__icontains=search)
        )
        show_all_tables = True

    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.filter(status=1).exclude(status=9).count() + FamilyHead.objects.filter(status=1).exclude(status=9).count()
    inactive_members = FamilyMember.objects.filter(status=0).exclude(status=9).count() + FamilyHead.objects.filter(status=0).exclude(status=9).count()
    deleted = FamilyMember.objects.filter(status=9).count() + FamilyHead.objects.filter(status=9).count()

    head_page = request.GET.get('head_page', 1)
    family_page = request.GET.get('family_page', 1)
    state_page = request.GET.get('state_page', 1)
    city_page = request.GET.get('city_page', 1)

    head_paginator = Paginator(heads, 10)
    family_paginator = Paginator(families, 10)
    state_paginator = Paginator(states, 10)
    city_paginator = Paginator(filtered_cities, 10)

    context = {
        'search': search,
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
        'show_all_tables': show_all_tables,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dashboard_family.html', context, content_type='text/html')
    return render(request, 'dashboard_family.html', context)


@login_required(login_url='login')
def dashboard_state(request):
    # Define variables and initialize querysets at the beginning
    search = request.GET.get('search', '').strip()
    state_filter = request.GET.get('state_filter', '')

    heads = FamilyHead.objects.exclude(status=9)
    families = FamilyMember.objects.exclude(status=9)
    states = State.objects.exclude(status=9) if hasattr(State, 'status') else State.objects.all()
    all_states = State.objects.exclude(status=9)
    if state_filter:
        filtered_cities = City.objects.exclude(status=9).filter(state_id=state_filter, country_id=101)
    else:
        filtered_cities = City.objects.exclude(status=9).filter(country_id=101)

    show_all_tables = False
    if search:
        heads = heads.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(State__icontains=search) |
            Q(City__icontains=search) |
            Q(Address__icontains=search)
        )
        families = families.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(Relationship__icontains=search)
        )
        states = states.filter(Q(name__icontains=search))
        filtered_cities = filtered_cities.filter(Q(name__icontains=search))
        show_all_tables = True

    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.filter(status=1).exclude(status=9).count() + FamilyHead.objects.filter(status=1).exclude(status=9).count()
    inactive_members = FamilyMember.objects.filter(status=0).exclude(status=9).count() + FamilyHead.objects.filter(status=0).exclude(status=9).count()
    deleted = FamilyMember.objects.filter(status=9).count() + FamilyHead.objects.filter(status=9).count()

    head_page = request.GET.get('head_page', 1)
    family_page = request.GET.get('family_page', 1)
    state_page = request.GET.get('state_page', 1)
    city_page = request.GET.get('city_page', 1)

    from django.core.paginator import EmptyPage
    head_paginator = Paginator(heads, 10)
    family_paginator = Paginator(families, 10)
    state_paginator = Paginator(states, 10)
    city_paginator = Paginator(filtered_cities, 10)

    try:
        head_page_obj = head_paginator.get_page(head_page)
    except EmptyPage:
        head_page_obj = head_paginator.get_page(1)
    try:
        family_page_obj = family_paginator.get_page(family_page)
    except EmptyPage:
        family_page_obj = family_paginator.get_page(1)
    try:
        state_page_obj = state_paginator.get_page(state_page)
    except EmptyPage:
        state_page_obj = state_paginator.get_page(1)
    try:
        city_page_obj = city_paginator.get_page(city_page)
    except EmptyPage:
        city_page_obj = city_paginator.get_page(1)

    context = {
        'search': search,
        'head_page_obj': head_page_obj,
        'family_page_obj': family_page_obj,
        'state_page_obj': state_page_obj,
        'city_page_obj': city_page_obj,
        'total_families': total_families,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'deleted': deleted,
        'username': request.user.username if request.user.is_authenticated else '',
        'all_states': all_states,
        'show_all_tables': show_all_tables,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dashboard_state.html', context, content_type='text/html')
    return render(request, 'dashboard_state.html', context)



from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import FamilyHead, FamilyMember, State, City
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def dashboard_city(request):
    # Define variables and initialize querysets at the beginning
    search = request.GET.get('search', '').strip()
    state_filter = request.GET.get('state_filter', '')

    heads = FamilyHead.objects.exclude(status=9)
    families = FamilyMember.objects.exclude(status=9)
    states = State.objects.exclude(status=9) if hasattr(State, 'status') else State.objects.all()
    all_states = State.objects.exclude(status=9)
    if state_filter:
        filtered_cities = City.objects.exclude(status=9).filter(state_id=state_filter, country_id=101)
    else:
        filtered_cities = City.objects.exclude(status=9).filter(country_id=101)


    show_all_tables = False 
    if search:
        heads = heads.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(State__icontains=search) |
            Q(City__icontains=search) |
            Q(Address__icontains=search)
        )
        families = families.filter(
            Q(Name__icontains=search) |
            Q(Surname__icontains=search) |
            Q(MobileNo__icontains=search) |
            Q(Relationship__icontains=search)
        )
        states = states.filter(Q(name__icontains=search))
        filtered_cities = filtered_cities.filter(Q(name__icontains=search))
        show_all_tables = True

    total_families = FamilyHead.objects.exclude(status=9).count()
    total_members = FamilyMember.objects.exclude(status=9).count() + FamilyHead.objects.exclude(status=9).count()
    active_members = FamilyMember.objects.filter(status=1).exclude(status=9).count() + FamilyHead.objects.filter(status=1).exclude(status=9).count()
    inactive_members = FamilyMember.objects.filter(status=0).exclude(status=9).count() + FamilyHead.objects.filter(status=0).exclude(status=9).count()
    deleted = FamilyMember.objects.filter(status=9).count() + FamilyHead.objects.filter(status=9).count()

    head_page = request.GET.get('head_page', 1)
    family_page = request.GET.get('family_page', 1)
    state_page = request.GET.get('state_page', 1)
    city_page = request.GET.get('city_page', 1)
    
    head_paginator = Paginator(heads, 10)
    family_paginator = Paginator(families, 10)
    state_paginator = Paginator(states, 10)
    city_paginator = Paginator(filtered_cities, 10)

    context = {
        'search': search,
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
        'show_all_tables': show_all_tables,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dashboard_city.html', context, content_type='text/html')
    return render(request, 'dashboard_city.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        AdminLog.objects.create(
            user=request.user,
            username=request.user.username,
            action='logout',
            description='Admin logged out',
            object_id=str(request.user.id),
            object_type='User'
        )
    logout(request)
    # messages.success(request, 'Logout successful!')
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
                messages.success(request, 'Password changed successfully!')
                return redirect('login_view')
            else:
                for error in errors:
                    messages.error(request, error)
                return redirect('reset-password', reset_id=reset_id)

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'reset_password.html')