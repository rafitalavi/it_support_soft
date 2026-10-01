from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # IT Assets
    path('assets/', views.asset_list_view, name='asset-list'),
    path('assets/add/', views.asset_create_view, name='asset-create'),
    path('assets/<int:pk>/', views.asset_detail_view, name='asset-detail'),
    path('assets/<int:pk>/edit/', views.asset_edit_view, name='asset-edit'),
    path('assets/<int:asset_id>/reassign/', views.reassign_view, name='asset-reassign'),
    path('assets/<int:asset_id>/return/', views.asset_return_view, name='asset-return'),
    path('reassign/', views.reassign_view, name='reassign'),

    # Employees
    path('employees/', views.employee_list_view, name='employee-list'),
    path('employees/add/', views.employee_create_view, name='employee-create'),
    path('employees/<int:pk>/', views.employee_detail_view, name='employee-detail'),
    path('employees/<int:pk>/edit/', views.employee_edit_view, name='employee-edit'),
    path('designations/add-ajax/', views.designation_create_ajax_view, name='designation-create-ajax'),

    # Audit History
    path('history/', views.history_list_view, name='history-list'),
]
