from django.urls import path
from . import views

urlpatterns = [
    path('ip-phones/', views.ip_phone_list_view, name='ip-phone-list'),
    path('ip-phones/add/', views.ip_phone_create_view, name='ip-phone-create'),
    path('ip-phones/<int:pk>/', views.ip_phone_detail_view, name='ip-phone-detail'),
    path('ip-phones/<int:pk>/edit/', views.ip_phone_edit_view, name='ip-phone-edit'),
    path('ip-phones/<int:pk>/delete/', views.ip_phone_delete_view, name='ip-phone-delete'),
]
