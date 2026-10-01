from django.urls import path, include
from rest_framework.routers import DefaultRouter
# pyrefly: ignore [missing-import]
from .api_views import (
    EmployeeViewSet,
    ITAssetViewSet,
    AssetAssignmentHistoryViewSet,
    DashboardStatsAPIView,
)
from user_ip_phones.api_views import UserIPPhonesViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='api-employee')
router.register(r'assets', ITAssetViewSet, basename='api-asset')
router.register(r'history', AssetAssignmentHistoryViewSet, basename='api-history')
router.register(r'ip-phones', UserIPPhonesViewSet, basename='api-ip-phones')

urlpatterns = [
    path('stats/', DashboardStatsAPIView.as_view(), name='api-stats'),
    path('', include(router.urls)),
]
