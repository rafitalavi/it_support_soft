from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import user_ip_phones_informations
from .forms import UserIPPhonesForm


@login_required
def ip_phone_list_view(request):
    """
    Directory of all registered IP Phones and extension allocations.
    """
    query = request.GET.get('q', '').strip()
    section_filter = request.GET.get('section', '').strip()

    phones = user_ip_phones_informations.objects.select_related(
        'employee', 'user', 'created_by'
    ).all().order_by('-created_at')

    if query:
        phones = phones.filter(
            Q(ip_phone_no__icontains=query) |
            Q(ip_phone_model__icontains=query) |
            Q(ip_phone_mac_address__icontains=query) |
            Q(ip_phone_ip_address__icontains=query) |
            Q(section__icontains=query) |
            Q(work_station__icontains=query) |
            Q(employee__name__icontains=query) |
            Q(employee__employee_id__icontains=query)
        )

    if section_filter:
        phones = phones.filter(section__iexact=section_filter)

    sections = user_ip_phones_informations.objects.values_list('section', flat=True).distinct()

    paginator = Paginator(phones, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'section_filter': section_filter,
        'sections': sorted([s for s in sections if s]),
        'total_count': phones.count(),
    }
    return render(request, 'ip_phones/ip_phone_list.html', context)


@login_required
def ip_phone_detail_view(request, pk):
    """
    Detailed hardware, network, and employee profile for an IP Phone.
    """
    phone = get_object_or_404(
        user_ip_phones_informations.objects.select_related('employee', 'user', 'created_by', 'updated_by'),
        pk=pk
    )
    return render(request, 'ip_phones/ip_phone_detail.html', {'phone': phone})


@login_required
def ip_phone_create_view(request):
    """
    Register a new IP phone and assign it to an employee / workstation.
    """
    if request.method == 'POST':
        form = UserIPPhonesForm(request.POST)
        if form.is_valid():
            phone = form.save(commit=False)
            user = request.user if request.user.is_authenticated else None
            phone.created_by = user
            phone.updated_by = user
            phone.save()
            messages.success(
                request,
                f"IP Phone '{phone.ip_phone_no}' assigned to {phone.employee.name} registered successfully!"
            )
            return redirect('ip-phone-detail', pk=phone.pk)
    else:
        # Pre-select employee if passed in query param
        initial = {}
        emp_id = request.GET.get('employee')
        if emp_id:
            initial['employee'] = emp_id
        form = UserIPPhonesForm(initial=initial)

    return render(request, 'ip_phones/ip_phone_form.html', {
        'form': form,
        'title': 'Register New IP Phone',
    })


@login_required
def ip_phone_edit_view(request, pk):
    """
    Edit IP Phone details, workstation location, or network parameters.
    """
    phone = get_object_or_404(user_ip_phones_informations, pk=pk)

    if request.method == 'POST':
        form = UserIPPhonesForm(request.POST, instance=phone)
        if form.is_valid():
            phone = form.save(commit=False)
            user = request.user if request.user.is_authenticated else None
            phone.updated_by = user
            phone.save()
            messages.success(request, f"IP Phone '{phone.ip_phone_no}' updated successfully!")
            return redirect('ip-phone-detail', pk=phone.pk)
    else:
        form = UserIPPhonesForm(instance=phone)

    return render(request, 'ip_phones/ip_phone_form.html', {
        'form': form,
        'phone': phone,
        'title': f'Edit IP Phone: {phone.ip_phone_no}',
    })


@login_required
def ip_phone_delete_view(request, pk):
    """
    Delete an IP phone record with confirmation.
    """
    phone = get_object_or_404(user_ip_phones_informations, pk=pk)
    if request.method == 'POST':
        phone_no = phone.ip_phone_no
        phone.delete()
        messages.success(request, f"IP Phone record '{phone_no}' has been deleted.")
        return redirect('ip-phone-list')

    return render(request, 'ip_phones/ip_phone_confirm_delete.html', {'phone': phone})
