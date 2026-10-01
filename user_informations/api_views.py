from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

# pyrefly: ignore [missing-import]
from .models import Employee, ITAsset, AssetAssignmentHistory
# pyrefly: ignore [missing-import]
from .serializers import (
    EmployeeSerializer,
    EmployeeDetailSerializer,
    ITAssetSerializer,
    ITAssetDetailSerializer,
    AssetAssignmentHistorySerializer,
    AssetReassignSerializer,
)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing employees.
    """
    queryset = Employee.objects.all().order_by('employee_id')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_id', 'name', 'department', 'email_address', 'floor', 'ip_extension']
    ordering_fields = ['employee_id', 'name', 'department', 'created_at']

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return EmployeeDetailSerializer
        return EmployeeSerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(updated_by=user)


class ITAssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing IT assets, with custom actions for reassignment and returning to stock.
    """
    queryset = ITAsset.objects.select_related('current_employee').all().order_by('asset_no')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'asset_no',
        'device_name',
        'device_type',
        'ip_address',
        'po_no',
        'current_employee__name',
        'current_employee__employee_id'
    ]
    ordering_fields = ['asset_no', 'device_name', 'status', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        device_type_param = self.request.query_params.get('device_type')
        if device_type_param:
            qs = qs.filter(device_type__icontains=device_type_param)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ITAssetDetailSerializer
        if self.action == 'reassign':
            return AssetReassignSerializer
        return ITAssetSerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        asset = serializer.save(created_by=user, updated_by=user)
        # If assigned during creation, create history
        if asset.current_employee:
            asset.reassign_to(
                new_employee=asset.current_employee,
                assigned_by=user,
                remarks=f"Initial assignment to {asset.current_employee.name}"
            )

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(updated_by=user)

    @action(detail=True, methods=['post'])
    def reassign(self, request, pk=None):
        """
        POST /api/assets/{id}/reassign/
        Payload: {"employee_id": "EMP001", "remarks": "Hardware transfer"}
        """
        asset = self.get_object()
        serializer = AssetReassignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emp_identifier = serializer.validated_data['employee_id']
        remarks = serializer.validated_data.get('remarks', '')

        # Lookup employee by pk or employee_id
        employee = Employee.objects.filter(
            Q(pk=emp_identifier if str(emp_identifier).isdigit() else -1) |
            Q(employee_id__iexact=str(emp_identifier).strip())
        ).first()

        if not employee:
            return Response(
                {"error": f"Employee with identifier '{emp_identifier}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        assigned_by = request.user if request.user.is_authenticated else None
        asset.reassign_to(new_employee=employee, assigned_by=assigned_by, remarks=remarks)

        return Response({
            "message": f"Asset {asset.asset_no} successfully assigned to {employee.name} ({employee.employee_id}).",
            "asset": ITAssetDetailSerializer(asset).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def return_asset(self, request, pk=None):
        """
        POST /api/assets/{id}/return_asset/
        Payload: {"remarks": "Returned for maintenance"}
        """
        asset = self.get_object()
        remarks = request.data.get('remarks', 'Returned to IT inventory')
        returned_by = request.user if request.user.is_authenticated else None

        if not asset.current_employee:
            return Response(
                {"message": f"Asset {asset.asset_no} is already unassigned / in stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        previous_emp = asset.current_employee.name
        asset.return_to_inventory(returned_by=returned_by, remarks=remarks)

        return Response({
            "message": f"Asset {asset.asset_no} returned from {previous_emp} to stock.",
            "asset": ITAssetDetailSerializer(asset).data
        }, status=status.HTTP_200_OK)


class AssetAssignmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing chronological asset assignment history and audit logs.
    """
    queryset = AssetAssignmentHistory.objects.select_related('asset', 'employee').all().order_by('-assigned_date')
    serializer_class = AssetAssignmentHistorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'asset__asset_no',
        'asset__device_name',
        'employee__name',
        'employee__employee_id',
        'remarks'
    ]
    ordering_fields = ['assigned_date', 'returned_date', 'is_current']

    def get_queryset(self):
        qs = super().get_queryset()
        asset_id = self.request.query_params.get('asset_id')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        is_current = self.request.query_params.get('is_current')
        if is_current is not None:
            val = is_current.lower() in ('true', '1')
            qs = qs.filter(is_current=val)
        return qs


class DashboardStatsAPIView(APIView):
    """
    GET /api/stats/
    Returns real-time counts and stats for the dashboard.
    """
    def get(self, request):
        total_assets = ITAsset.objects.count()
        assigned_assets = ITAsset.objects.filter(status='ASSIGNED').count()
        available_assets = ITAsset.objects.filter(status='AVAILABLE').count()
        maintenance_assets = ITAsset.objects.filter(status='MAINTENANCE').count()
        retired_assets = ITAsset.objects.filter(status='RETIRED').count()
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()

        recent_history = AssetAssignmentHistory.objects.select_related('asset', 'employee').order_by('-assigned_date')[:5]

        return Response({
            "total_assets": total_assets,
            "assigned_assets": assigned_assets,
            "available_assets": available_assets,
            "maintenance_assets": maintenance_assets,
            "retired_assets": retired_assets,
            "total_employees": total_employees,
            "active_employees": active_employees,
            "recent_transfers": AssetAssignmentHistorySerializer(recent_history, many=True).data
        })
