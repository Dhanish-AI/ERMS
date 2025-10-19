from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import AdminLoginForm, EmployeeCreateForm, EmployeeLoginForm, EmployeeUpdateForm
from .models import Employee


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url="admin_login")(view_func)


def employee_required(view_func):
    def check(user):
        return user.is_authenticated and not user.is_staff and hasattr(user, "employee_profile")

    return user_passes_test(check, login_url="employee_login")(view_func)


def redirect_authenticated_user(user):
    if user.is_staff:
        return reverse("admin_dashboard")
    if hasattr(user, "employee_profile"):
        return reverse("employee_dashboard")
    return None


def login_view(request: HttpRequest, form_class: type[AuthenticationForm], template: str, role: str) -> HttpResponse:
    if request.user.is_authenticated:
        redirect_url = redirect_authenticated_user(request.user)
        if redirect_url:
            return redirect(redirect_url)

    form = form_class(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            redirect_url = redirect_authenticated_user(user)
            return redirect(redirect_url or "home")

    return render(
        request,
        template,
        {
            "form": form,
            "role": role,
        },
    )


def admin_login(request: HttpRequest) -> HttpResponse:
    return login_view(request, AdminLoginForm, "registration/login.html", role="admin")


def employee_login(request: HttpRequest) -> HttpResponse:
    return login_view(request, EmployeeLoginForm, "registration/login.html", role="employee")


def logout_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect("home")


def home(request: HttpRequest) -> HttpResponse:
    redirect_url = redirect_authenticated_user(request.user)
    if redirect_url:
        return redirect(redirect_url)
    return render(request, "home.html")


@admin_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    all_employees = list(Employee.objects.all())
    total_employees = len(all_employees)
    full_time_count = sum(1 for employee in all_employees if employee.full_time)
    department_count = len({employee.department for employee in all_employees if employee.department})

    query = request.GET.get("q", "").strip()
    employees_qs = Employee.objects.all()
    if query:
        employees_qs = employees_qs.filter(
            Q(employee_id__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(department__icontains=query)
            | Q(role__icontains=query)
        )

    employees = employees_qs.order_by("employee_id")
    context = {
        "employees": employees,
        "employees_count": total_employees,
        "full_time_count": full_time_count,
        "department_count": department_count,
        "query": query,
    }
    return render(request, "employees/admin_dashboard.html", context)


@employee_required
def employee_dashboard(request: HttpRequest) -> HttpResponse:
    employee = request.user.employee_profile
    return render(request, "employees/employee_dashboard.html", {"employee": employee})


@admin_required
def employee_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Employee {employee.full_name} was created successfully.")
            return redirect("admin_dashboard")
    else:
        form = EmployeeCreateForm()

    return render(
        request,
        "employees/employee_form.html",
        {
            "form": form,
            "title": "Add Employee",
            "submit_label": "Create Employee",
        },
    )


@admin_required
def employee_update(request: HttpRequest, pk: int) -> HttpResponse:
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Employee {employee.full_name} was updated successfully.")
            return redirect("employee_detail", pk=employee.pk)
    else:
        form = EmployeeUpdateForm(instance=employee)

    return render(
        request,
        "employees/employee_form.html",
        {
            "form": form,
            "title": "Edit Employee",
            "submit_label": "Save Changes",
            "employee": employee,
        },
    )


@admin_required
def employee_detail(request: HttpRequest, pk: int) -> HttpResponse:
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, "employees/employee_detail.html", {"employee": employee})


@admin_required
def employee_delete(request: HttpRequest, pk: int) -> HttpResponse:
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        full_name = employee.full_name
        user = employee.user
        employee.delete()
        if user:
            user.delete()
        messages.success(request, f"Employee {full_name} was deleted successfully.")
        return redirect("admin_dashboard")

    return render(
        request,
        "employees/employee_confirm_delete.html",
        {
            "employee": employee,
        },
    )
