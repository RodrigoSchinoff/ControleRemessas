from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home(request):
    # placeholder temporário – só confirma que o login funcionou
    return render(request, "core/home.html")

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')  # usa o name 'login' que você já tem
