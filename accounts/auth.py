from functools import wraps

from django.shortcuts import redirect


def _role_redirect_name(request, staff_target='admin-dashboard', user_target='homepage'):
    if not request.user.is_authenticated:
        return None
    return staff_target if request.user.is_staff else user_target


# give access to admin page if request comes from admin
# if request is from normal user redirect to user page

def admin_only(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return redirect('homepage')
    return wrapper_func


# give access to user pages if request comes from user
# if request is from admin redirect to admin_dashboard

def user_only(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin-dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper_func
