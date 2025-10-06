from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # ======= CHI PHÍ (Expense) =======
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/new/", views.expense_create, name="expense_create"),
    path("expenses/<int:pk>/", views.expense_detail, name="expense_detail"),
    path("expenses/<int:pk>/edit/", views.expense_update, name="expense_update"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="expense_delete"),

    # ======= DOANH THU (Revenue) =======
    path("revenues/", views.revenue_list, name="revenue_list"),
    path("revenues/new/", views.revenue_create, name="revenue_create"),
    path("revenues/<int:pk>/", views.revenue_detail, name="revenue_detail"),
    path("revenues/<int:pk>/edit/", views.revenue_update, name="revenue_update"),
    path("revenues/<int:pk>/delete/", views.revenue_delete, name="revenue_delete"),

    # ======= BẢNG LƯƠNG (Payroll) =======
    path("payrolls/", views.payroll_list, name="payroll_list"),
    path("payrolls/new/", views.payroll_create, name="payroll_create"),
    path("payrolls/<int:pk>/", views.payroll_detail, name="payroll_detail"),
    path("payrolls/<int:pk>/edit/", views.payroll_update, name="payroll_update"),
    path("payrolls/<int:pk>/regenerate/", views.payroll_regenerate, name="payroll_regenerate"),
    path("payrolls/<int:pk>/approve/", views.payroll_approve, name="payroll_approve"),
    path("payrolls/<int:pk>/delete/", views.payroll_delete, name="payroll_delete"),
]