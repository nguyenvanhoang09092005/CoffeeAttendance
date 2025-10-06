from django.contrib import admin
from .models import Employee,EmployeeFace

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id',
        'first_name',
        'last_name',
        'email',
        'gender',
        'date_of_birth',
        'position',
        'joining_date',
        'mobile_number',
        'address',
        'bank_account_number',
        'bank_name',
        'employment_status',
        'resignation_date'
    )
    search_fields = (
        'employee_id',
        'first_name',
        'last_name',
        'position',
    )
    list_filter = (
        'gender',
        'position',
        'employment_status'
    )
    readonly_fields = ('employee_image',)

@admin.register(EmployeeFace)
class EmployeeFaceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'created_at')