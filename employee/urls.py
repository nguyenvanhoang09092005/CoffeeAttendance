from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.employee_list, name='employee_list'),
    path("add/", views.add_employee, name="add_employee"),
    path('employees/<str:slug>/', views.view_employee, name='view_employee'),
    path('edit/<str:slug>/', views.edit_employee, name='edit_employee'),
    path('delete/<str:slug>/', views.delete_employee, name='delete_employee'),
]
