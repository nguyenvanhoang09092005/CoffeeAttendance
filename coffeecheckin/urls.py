from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
   path('',views.index, name="index"),
   # path('dashboard/', views.dashboard, name='dashboard'), 
   path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
   path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
   path('notification/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read' ),
   path('notification/clear-all', views.clear_all_notification, name= "clear_all_notification")


]
