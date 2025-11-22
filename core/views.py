from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home(request):
    # placeholder temporário – só confirma que o login funcionou
    return render(request, "core/home.html")
