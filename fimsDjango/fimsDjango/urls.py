from django.contrib import admin
from django.urls import path
from fims.views import *


urlpatterns = [
    path('', home, name='home'),
    path('base/', base, name='base'),
    path('regis/', regis, name='regis'),
    path('stats/', stats, name='stats'),
    path('login/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path("state/", state, name="state"),
    path("city/", city, name="city"),
    path('admin/', admin.site.urls),
    path('forgot-password/', ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', ResetPassword, name='reset-password'),
    path('update-status/', update_status, name='update-status'),
    path('head/edit/<int:id>/', update_head, name='update_head'),
    path('state/edit/<int:id>/', edit_state, name='edit_state'),
    path('city/edit/<int:id>/', edit_city, name='edit_city'),
    path('add_state/', add_state, name='add_state'),
    path('add_city/', add_city, name='add_city'),
    path('view_family/<int:id>/', view_family, name='view_family'),
    path('view_state/<int:id>/', view_state, name='view_state'),

]