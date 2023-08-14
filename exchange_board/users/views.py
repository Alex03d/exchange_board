# views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .models import Invitation, CustomUser


def register(request, invite_code):
    # Проверка наличия приглашения
    try:
        invitation = Invitation.objects.get(code=invite_code, used=False)
    except Invitation.DoesNotExist:
        return render(request, 'error.html', {'message': 'Invalid or used invitation code.'})

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Отметить приглашение как использованное
            invitation.used = True
            invitation.save()
            # Уменьшить количество доступных приглашений у пригласившего пользователя
            inviter = invitation.inviter
            inviter.invites_left -= 1
            inviter.save()
            return redirect('login')  # Redirect to login page or any other page
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def create_invite(request):
    user = request.user
    if user.invites_left > 0:
        Invitation.objects.create(inviter=user)
        user.invites_left -= 1
        user.save()
        return redirect('dashboard')  # Redirect to dashboard or any other page
    else:
        return render(request, 'error.html', {'message': 'No invitations left.'})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Или другую страницу после успешного входа
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')
