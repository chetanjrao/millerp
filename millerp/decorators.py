from django.shortcuts import redirect, resolve_url

def check_owner_role(view_function):
    def wrapper(request, *args, **kwargs):
        if request.user.role == 3:
            return view_function(request, *args, **kwargs)
        else:
            return redirect(resolve_url('login'))
    return wrapper