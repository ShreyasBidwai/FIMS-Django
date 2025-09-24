from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from fims.views import *
from fims.excel_export import excel_view


urlpatterns = [
    path('fims/check_city_name_unique/', check_city_name_unique, name='check_city_name_unique'),
    path('fims/check_state_name_unique/', check_state_name_unique, name='check_state_name_unique'),
    path('fims/check_head_mobile_unique/', check_head_mobile_unique, name='check_head_mobile_unique'),
    path('', home, name='home'),
    path('base/', base, name='base'),
    path('regis/', regis, name='regis'),
    path('stats/', stats, name='stats'),
    path('login/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout'),
    path('dashboard_head/', dashboard_head, name='dashboard_head'),
    path('dashboard_family/', dashboard_family, name='dashboard_family'),
    path('dashboard_state/', dashboard_state, name='dashboard_state'),
    path('dashboard_city/', dashboard_city, name='dashboard_city'),
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
    path('pdf_view/', pdf_view, name='pdf_view'),
    path('excel_view/', excel_view, name='excel_view'),
    path('export_heads_excel/', export_heads_excel, name='export_heads_excel'),
    path('dashboard-stats-api/', dashboard_stats_api, name='dashboard_stats_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
