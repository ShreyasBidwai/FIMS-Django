from django.contrib import admin
from .models import * 
from .models import PasswordReset

admin.site.register(PasswordReset)
admin.site.register(FamilyHead)
admin.site.register(FamilyMember)
admin.site.register(Hobby)
