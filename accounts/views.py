from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('signup_complete')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def signup_complete(request):
    return render(request, 'accounts/signup_complete.html')

