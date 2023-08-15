# views.py
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import CustomUserCreationForm
from .models import Invitation, CustomUser


def register(request, invite_code):
    # Проверка наличия приглашения
    try:
        invitation = Invitation.objects.get(code=invite_code, used=False)
    except Invitation.DoesNotExist:
        return render(request, 'error.html', {'message': 'Invalid or used invitation code.'})

    inviter = invitation.inviter
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Сначала не сохраняем пользователя
            user.invited_by = invitation.inviter  # Устанавливаем пользователя, который отправил приглашение

            # Логика генерации уникального кода
            if user.invited_by.is_superuser:
                # Если пользователь приглашен суперпользователем
                next_code = CustomUser.objects.filter(invited_by=user.invited_by).count() + 1
                user.referral_code = str(next_code)
            else:
                # Если пользователь приглашен не суперпользователем
                ancestors = []
                inviter = user.invited_by
                while inviter and not inviter.is_superuser:  # Убираем суперпользователя из цепочки
                    ancestors.append(inviter.referral_code.split('-')[-1])
                    inviter = inviter.invited_by
                ancestors.reverse()
                next_sub_code = CustomUser.objects.filter(invited_by=user.invited_by).count() + 1
                ancestors.append(str(next_sub_code))
                user.referral_code = '-'.join(ancestors)

            user.save()
            # Отметить приглашение как использованное
            invitation.used = True
            invitation.save()
            # Уменьшить количество доступных приглашений у пригласившего пользователя
            if not inviter.is_superuser:
                inviter.invites_left -= 1
                inviter.save()
            return redirect('login')  # Redirect to login page or any other page
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

# def register(request, invite_code):
#     # Проверка наличия приглашения
#     try:
#         invitation = Invitation.objects.get(code=invite_code, used=False)
#     except Invitation.DoesNotExist:
#         return render(request, 'error.html', {'message': 'Invalid or used invitation code.'})
#
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)  # Сначала не сохраняем пользователя
#             user.invited_by = invitation.inviter  # Устанавливаем пользователя, который отправил приглашение
#
#             # Логика генерации уникального кода
#             if user.invited_by.is_superuser:
#                 # Если пользователь приглашен суперпользователем
#                 next_code = CustomUser.objects.filter(invited_by=user.invited_by).count() + 1
#                 user.referral_code = str(next_code)
#             else:
#                 # Если пользователь приглашен не суперпользователем
#                 ancestors = []
#                 inviter = user.invited_by
#                 while inviter and hasattr(inviter, 'referral_code') and inviter.referral_code:
#                     ancestors.append(inviter.referral_code.split('-')[-1])
#                     inviter = inviter.invited_by
#                 ancestors.reverse()
#                 next_sub_code = CustomUser.objects.filter(invited_by=user.invited_by).count() + 1
#                 ancestors.append(str(next_sub_code))
#                 user.referral_code = '-'.join(ancestors)
#
#             user.save()
#             # Отметить приглашение как использованное
#             invitation.used = True
#             invitation.save()
#             # Уменьшить количество доступных приглашений у пригласившего пользователя
#             inviter = invitation.inviter
#             inviter.invites_left -= 1
#             inviter.save()
#             return redirect('login')  # Redirect to login page or any other page
#     else:
#         form = CustomUserCreationForm()
#
#     return render(request, 'register.html', {'form': form})


# def create_invite(request):
#     user = request.user
#
#     # Проверяем количество созданных приглашений для этого пользователя
#     created_invites = Invitation.objects.filter(inviter=user).count()
#
#     if user.is_superuser or (created_invites < 3 and user.invites_left > 0):
#         new_invite = Invitation.objects.create(inviter=user)
#         if not user.is_superuser:
#             user.invites_left -= 1
#             user.save()
#         invite_link = request.build_absolute_uri(reverse('register_with_invite', kwargs={'invite_code': new_invite.code}))
#         return render(request, 'invite_link.html', {'invite_link': invite_link})
#     else:
#         return render(request, 'error.html', {'message': 'No invitations left.'})

def create_invite(request):
    user = request.user

    # Проверяем количество созданных приглашений для этого пользователя
    created_invites = Invitation.objects.filter(inviter=user).count()

    if user.is_superuser or (created_invites < 3 and user.invites_left > 0):
        new_invite = Invitation.objects.create(inviter=user)
        if not user.is_superuser:
            user.invites_left -= 1
            user.save()
        invite_link = request.build_absolute_uri(reverse('register_with_invite', kwargs={'invite_code': new_invite.code}))

        # Получаем все предыдущие приглашения этого пользователя
        previous_invitations = Invitation.objects.filter(inviter=user)

        return render(request, 'invite_link.html', {
            'invite_link': invite_link,
            'previous_invitations': previous_invitations
        })
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


def logout_view(request):
    logout(request)
    return redirect('index')


def handshake_count(code1, code2):
    parts1 = code1.split('-')
    parts2 = code2.split('-')

    # Сначала находим общую базу (какую часть пути они делят)
    common_base = 0
    while common_base < min(len(parts1), len(parts2)) and parts1[common_base] == parts2[common_base]:
        common_base += 1

    # Расчет количества рукопожатий:
    # количество шагов от первого пользователя до общей базы + количество шагов от второго пользователя до общей базы
    return (len(parts1) - common_base) + (len(parts2) - common_base) - 1
