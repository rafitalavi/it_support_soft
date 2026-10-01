from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone, dateformat
# pyrefly: ignore [missing-import]
from .models import Employee, ITAsset, AssetAssignmentHistory, Designation
# pyrefly: ignore [missing-import]
from .forms import EmployeeForm, ITAssetForm, ReassignAssetForm, ReturnAssetForm


@login_required
def dashboard_view(request):
    """
    Main Square IT Support & Asset Portal dashboard.
    """
    total_assets = ITAsset.objects.count()
    assigned_assets = ITAsset.objects.filter(status='ASSIGNED').count()
    available_assets = ITAsset.objects.filter(status='AVAILABLE').count()
    maintenance_assets = ITAsset.objects.filter(status='MAINTENANCE').count()
    total_employees = Employee.objects.count()

    recent_history = AssetAssignmentHistory.objects.select_related('asset', 'employee').order_by('-assigned_date')[:8]
    recent_assets = ITAsset.objects.select_related('current_employee').order_by('-created_at')[:6]

    context = {
        'total_assets': total_assets,
        'assigned_assets': assigned_assets,
        'available_assets': available_assets,
        'maintenance_assets': maintenance_assets,
        'total_employees': total_employees,
        'recent_history': recent_history,
        'recent_assets': recent_assets,
    }
    return render(request, 'dashboard.html', context)


@login_required
def asset_list_view(request):
    """
    List all IT assets with search and status filtering.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    device_type_filter = request.GET.get('device_type', '').strip()

    assets = ITAsset.objects.select_related('current_employee').all().order_by('asset_no')

    if query:
        assets = assets.filter(
            Q(asset_no__icontains=query) |
            Q(device_name__icontains=query) |
            Q(ip_address__icontains=query) |
            Q(po_no__icontains=query) |
            Q(current_employee__name__icontains=query) |
            Q(current_employee__employee_id__icontains=query)
        )

    if status_filter:
        assets = assets.filter(status=status_filter.upper())

    if device_type_filter:
        assets = assets.filter(device_type__icontains=device_type_filter)

    paginator = Paginator(assets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    device_types = ITAsset.objects.values_list('device_type', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'device_type_filter': device_type_filter,
        'device_types': [dt for dt in device_types if dt],
        'status_choices': ITAsset.AssetStatus.choices,
    }
    return render(request, 'assets/asset_list.html', context)


@login_required
def asset_detail_view(request, pk):
    """
    Detailed view of an IT asset including its current employee and historical users.
    """
    asset = get_object_or_404(ITAsset.objects.select_related('current_employee'), pk=pk)
    history = asset.assignment_history.select_related('employee', 'assigned_by', 'returned_by').order_by('-assigned_date')

    history_data = {}
    for record in history:
        assigned_dt = timezone.localtime(record.assigned_date) if record.assigned_date else None
        returned_dt = timezone.localtime(record.returned_date) if record.returned_date else None
        history_data[str(record.id)] = {
            'id': str(record.id),
            'employeeName': record.employee.name if record.employee else '',
            'employeeId': record.employee.employee_id if record.employee else '',
            'department': (record.employee.department if record.employee and record.employee.department else 'Not specified'),
            'floor': (record.employee.floor if record.employee and record.employee.floor else '-'),
            'email': (record.employee.email_address if record.employee and record.employee.email_address else '-'),
            'ipExtension': (record.employee.ip_extension if record.employee and record.employee.ip_extension else '-'),
            'assignedDate': dateformat.format(assigned_dt, 'F d, Y - h:i A') if assigned_dt else '',
            'returnedDate': dateformat.format(returned_dt, 'F d, Y - h:i A') if returned_dt else 'Still In Active Possession',
            'isCurrent': bool(record.is_current),
            'duration': record.duration_display,
            'assignedBy': str(record.assigned_by) if record.assigned_by else 'System Admin',
            'returnedBy': str(record.returned_by) if record.returned_by else '-',
            'remarks': record.remarks or 'No specific remarks logged.',
        }

    context = {
        'asset': asset,
        'history': history,
        'history_data': history_data,
    }
    return render(request, 'assets/asset_detail.html', context)


@login_required
def asset_create_view(request):
    """
    Register a new IT asset into inventory.
    """
    if request.method == 'POST':
        form = ITAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            user = request.user if request.user.is_authenticated else None
            asset.created_by = user
            asset.updated_by = user
            assigned_emp = asset.current_employee
            asset.current_employee = None
            asset.save()

            if assigned_emp:
                asset.reassign_to(
                    new_employee=assigned_emp,
                    assigned_by=user,
                    remarks=f"Initial assignment to {assigned_emp.name}"
                )

            messages.success(request, f"Asset '{asset.asset_no}' created successfully!")
            return redirect('asset-detail', pk=asset.pk)
    else:
        form = ITAssetForm()

    return render(request, 'assets/asset_form.html', {'form': form, 'title': 'Add New IT Asset'})


@login_required
def asset_edit_view(request, pk):
    """
    Edit asset specifications. Note: Employee assignment changes trigger history automatically.
    """
    asset = get_object_or_404(ITAsset, pk=pk)
    if request.method == 'POST':
        old_emp = asset.current_employee
        form = ITAssetForm(request.POST, instance=asset)
        if form.is_valid():
            user = request.user if request.user.is_authenticated else None
            updated_asset = form.save(commit=False)
            new_emp = updated_asset.current_employee
            # Temporarily restore old_emp on instance so reassign_to detects change and archives old_emp
            updated_asset.current_employee = old_emp
            updated_asset.updated_by = user
            updated_asset.save()

            if old_emp != new_emp:
                if new_emp:
                    remarks = f"Reassigned from {old_emp.name if old_emp else 'Inventory'} to {new_emp.name}"
                    updated_asset.reassign_to(new_emp, assigned_by=user, remarks=remarks)
                else:
                    remarks = f"Returned to inventory from {old_emp.name if old_emp else 'Unknown'}"
                    updated_asset.return_to_inventory(returned_by=user, remarks=remarks)

            messages.success(request, f"Asset '{asset.asset_no}' updated successfully!")
            return redirect('asset-detail', pk=asset.pk)
    else:
        form = ITAssetForm(instance=asset)

    return render(request, 'assets/asset_form.html', {'form': form, 'title': f'Edit Asset: {asset.asset_no}'})


@login_required
def reassign_view(request, asset_id=None):
    """
    Dedicated view for transferring / reassigning an asset or returning it to stock.
    """
    selected_asset = None
    if asset_id:
        selected_asset = get_object_or_404(ITAsset, pk=asset_id)

    if request.method == 'POST':
        form = ReassignAssetForm(request.POST)
        if form.is_valid():
            asset = form.cleaned_data['asset']
            new_employee = form.cleaned_data['employee']
            returned_date = form.cleaned_data.get('returned_date')
            remarks = form.cleaned_data['remarks']
            user = request.user if request.user.is_authenticated else None

            if new_employee:
                old_emp_name = asset.current_employee.name if asset.current_employee else "Stock/Inventory"
                transfer_note = remarks or f"Transferred from {old_emp_name} to {new_employee.name}"
                asset.reassign_to(new_employee=new_employee, assigned_by=user, remarks=transfer_note)
                messages.success(request, f"Asset '{asset.asset_no}' successfully assigned to {new_employee.name} ({new_employee.employee_id})!")
            else:
                old_emp_name = asset.current_employee.name if asset.current_employee else "assigned user"
                return_note = remarks or f"Returned from {old_emp_name} to inventory"
                asset.return_to_inventory(returned_by=user, remarks=return_note, returned_date=returned_date)
                messages.info(request, f"Asset '{asset.asset_no}' has been returned to Inventory and is now AVAILABLE.")

            return redirect('asset-detail', pk=asset.pk)
    else:
        initial = {}
        if selected_asset:
            initial['asset'] = selected_asset
        form = ReassignAssetForm(initial=initial)

    return render(request, 'assets/reassign.html', {'form': form, 'selected_asset': selected_asset})


@login_required
def asset_return_view(request, asset_id):
    """
    Explicit view to process an asset return. Marks asset Available (or chosen status)
    and logs return timestamp, notes, and receiver.
    """
    asset = get_object_or_404(ITAsset.objects.select_related('current_employee'), pk=asset_id)

    if not asset.current_employee:
        messages.info(request, f"Asset '{asset.asset_no}' is already unassigned and available in inventory.")
        return redirect('asset-detail', pk=asset.pk)

    previous_holder = asset.current_employee

    if request.method == 'POST':
        form = ReturnAssetForm(request.POST)
        if form.is_valid():
            returned_date = form.cleaned_data.get('returned_date')
            new_status = form.cleaned_data.get('status', 'AVAILABLE')
            remarks = form.cleaned_data.get('remarks', '')
            user = request.user if request.user.is_authenticated else None

            final_remarks = remarks or f"Device returned from {previous_holder.name} back to stock."
            asset.return_to_inventory(
                returned_by=user,
                remarks=final_remarks,
                returned_date=returned_date,
                new_status=new_status
            )
            messages.success(
                request,
                f"Asset '{asset.asset_no}' successfully returned from {previous_holder.name}! Status updated to '{asset.get_status_display()}'."
            )
            return redirect('asset-detail', pk=asset.pk)
    else:
        form = ReturnAssetForm()

    return render(request, 'assets/asset_return.html', {
        'asset': asset,
        'previous_holder': previous_holder,
        'form': form,
    })


@login_required
def employee_list_view(request):
    """
    Directory of all employees.
    """
    query = request.GET.get('q', '').strip()
    dept = request.GET.get('department', '').strip()

    employees = Employee.objects.select_related('designation').prefetch_related('assigned_assets').all().order_by('employee_id')

    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query) |
            Q(name__icontains=query) |
            Q(designation__name__icontains=query) |
            Q(email_address__icontains=query) |
            Q(department__icontains=query) |
            Q(ip_extension__icontains=query)
        )

    if dept:
        employees = employees.filter(department__iexact=dept)

    departments = Employee.objects.values_list('department', flat=True).distinct()

    paginator = Paginator(employees, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'dept': dept,
        'departments': [d for d in departments if d],
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
def employee_detail_view(request, pk):
    """
    Profile of an employee showing currently assigned devices and past device history.
    """
    employee = get_object_or_404(Employee.objects.select_related('designation'), pk=pk)
    current_assets = employee.assigned_assets.all()
    past_history = employee.asset_history.select_related('asset').order_by('-assigned_date')

    context = {
        'employee': employee,
        'current_assets': current_assets,
        'past_history': past_history,
    }
    return render(request, 'employees/employee_detail.html', context)


@login_required
def employee_create_view(request):
    """
    Add a new employee.
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            emp = form.save(commit=False)
            user = request.user if request.user.is_authenticated else None
            emp.created_by = user
            emp.updated_by = user
            emp.save()
            messages.success(request, f"Employee '{emp.name}' ({emp.employee_id}) added successfully!")
            return redirect('employee-detail', pk=emp.pk)
    else:
        form = EmployeeForm()

    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Register New Employee'})


@login_required
def employee_edit_view(request, pk):
    """
    Edit employee details.
    """
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            user = request.user if request.user.is_authenticated else None
            emp = form.save(commit=False)
            emp.updated_by = user
            emp.save()
            messages.success(request, f"Employee '{emp.name}' updated successfully!")
            return redirect('employee-detail', pk=emp.pk)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'employees/employee_form.html', {'form': form, 'title': f'Edit Employee: {employee.name}'})


@login_required
def history_list_view(request):
    """
    Chronological audit trail of all asset reassignments and returns.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    history_qs = AssetAssignmentHistory.objects.select_related('asset', 'employee', 'assigned_by', 'returned_by').all().order_by('-assigned_date')

    if query:
        history_qs = history_qs.filter(
            Q(asset__asset_no__icontains=query) |
            Q(asset__device_name__icontains=query) |
            Q(employee__name__icontains=query) |
            Q(employee__employee_id__icontains=query) |
            Q(remarks__icontains=query)
        )

    if status_filter == 'active':
        history_qs = history_qs.filter(is_current=True)
    elif status_filter == 'returned':
        history_qs = history_qs.filter(is_current=False)

    paginator = Paginator(history_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'history/history_list.html', context)


@login_required
@require_POST
def designation_create_ajax_view(request):
    """
    Quick AJAX endpoint for creating a Designation on the fly from Employee Form.
    """
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Designation name cannot be empty.'}, status=400)

    designation, created = Designation.objects.get_or_create(name=name)
    return JsonResponse({
        'success': True,
        'id': designation.id,
        'name': designation.name,
        'created': created
    })

