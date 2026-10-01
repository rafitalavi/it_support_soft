from rest_framework import viewsets, filters
from .models import user_ip_phones_informations
from .serializers import UserIPPhonesSerializer


class UserIPPhonesViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user IP phones.
    Supports list, create, retrieve, update, and delete.
    """
    queryset = user_ip_phones_informations.objects.select_related('employee', 'user', 'created_by', 'updated_by').all().order_by('-created_at')
    serializer_class = UserIPPhonesSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'ip_phone_no',
        'ip_phone_model',
        'ip_phone_mac_address',
        'ip_phone_ip_address',
        'section',
        'work_station',
        'employee__name',
        'employee__employee_id',
    ]
    ordering_fields = ['ip_phone_no', 'section', 'created_at']

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(updated_by=user)
