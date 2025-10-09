from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # ======= LOẠI CHI PHÍ (ExpenseCategory) =======
    path('expense-categories/', views.expense_category_list, name='expense_category_list'),
    path('expense-categories/create/', views.expense_category_create, name='expense_category_create'),
    path('expense-categories/<int:pk>/', views.expense_category_detail, name='expense_category_detail'), 
    path('expense-categories/<int:pk>/update/', views.expense_category_update, name='expense_category_update'),
    path('expense-categories/<int:pk>/delete/', views.expense_category_delete, name='expense_category_delete'),
    
    # ======= CHI PHÍ ĐỘC LẬP (Expense) =======
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/new/", views.expense_create, name="expense_create"),
    path("expenses/<int:pk>/", views.expense_detail, name="expense_detail"),
    path("expenses/<int:pk>/edit/", views.expense_update, name="expense_update"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="expense_delete"),
    path("expenses/<int:pk>/approve/", views.expense_approve, name="expense_approve"),  
    path("expenses/<int:pk>/reject/", views.expense_reject, name="expense_reject"), 
    
    # ======= DOANH THU (Revenue) =======
    path("revenues/", views.revenue_list, name="revenue_list"),
    path("revenues/new/", views.revenue_create, name="revenue_create"),
    path("revenues/<int:pk>/", views.revenue_detail, name="revenue_detail"),
    path("revenues/<int:pk>/edit/", views.revenue_update, name="revenue_update"),
    path("revenues/<int:pk>/delete/", views.revenue_delete, name="revenue_delete"),
    
    # ======= CHI PHÍ LIÊN KẾT DOANH THU (RevenueExpense) =======
    path('revenues/<int:revenue_pk>/expenses/create/', views.revenue_expense_create, name='revenue_expense_create'),
    path('revenue-expenses/<int:pk>/edit/', views.revenue_expense_update, name='revenue_expense_update'),
    path('revenue-expenses/<int:pk>/delete/', views.revenue_expense_delete, name='revenue_expense_delete'),

    # ======= BẢNG LƯƠNG (Payroll) =======
    path("payrolls/", views.payroll_list, name="payroll_list"),
    path("payrolls/new/", views.payroll_create, name="payroll_create"),
    path("payrolls/<int:pk>/", views.payroll_detail, name="payroll_detail"),
    path("payrolls/<int:pk>/edit/", views.payroll_update, name="payroll_update"),
    path("payrolls/<int:pk>/regenerate/", views.payroll_regenerate, name="payroll_regenerate"),
    path("payrolls/<int:pk>/approve/", views.payroll_approve, name="payroll_approve"),
    path("payrolls/<int:pk>/delete/", views.payroll_delete, name="payroll_delete"),


    #---------------Nhân viên xem-------------------
    path('my-payroll/', views.my_payroll_list, name='my_payroll_list'),
    path('my-payroll/<int:pk>/', views.my_payroll_detail, name='my_payroll_detail'),
]