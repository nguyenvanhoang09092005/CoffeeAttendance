from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from .models import Notification

# Create your views here.

def index(request):
    return render(request, "authentication/login.html")

# def dashboard(request):
#     unread_notification = Notification.objects.filter(user=request.user, is_read=False)
#     unread_notification_count = unread_notification.count()
#     return render(request, "employees/employee-dashboard.html")

def admin_dashboard(request):
    unread_notification = Notification.objects.filter(user=request.user, is_read=False)
    unread_notification_count = unread_notification.count()
    return render(request, "Home/index.html", {
        'unread_count': unread_notification_count,
        'notifications': unread_notification,
    })


def staff_dashboard(request):
    unread_notification = Notification.objects.filter(user=request.user, is_read=False)
    unread_notification_count = unread_notification.count()
    return render(request, "staff/Dashboard/index.html", {
        'unread_count': unread_notification_count,
        'notifications': unread_notification,
    })


def mark_notification_as_read(request):
    if request.method == 'POST':
        notification = Notification.objects.filter(user=request.user, is_read=False)
        notification.update(is_read=True)
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden()

def clear_all_notification(request):
    if request.method == "POST":
        notification = Notification.objects.filter(user=request.user)
        notification.delete()
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden