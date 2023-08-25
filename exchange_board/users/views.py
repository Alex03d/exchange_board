from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import CustomUserCreationForm
from .models import Invitation, CustomUser, UserFollow


def register(request, invite_code):
    try:
        invitation = Invitation.objects.get(code=invite_code, used=False)
    except Invitation.DoesNotExist:
        return render(
            request,
            'error.html', {'message': 'Invalid or used invitation code.'}
        )

    inviter = invitation.inviter
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.invited_by = invitation.inviter

            next_sub_code = (
                    CustomUser.objects.filter(invited_by=inviter).count() + 1
            )
            user.referral_code = f"{inviter.referral_code}-{next_sub_code}"

            user.save()
            invitation.used = True
            invitation.save()
            if not inviter.is_superuser:
                inviter.invites_left -= 1
                inviter.save()
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


def create_invite(request):
    user = request.user

    created_invites = Invitation.objects.filter(inviter=user).count()

    if user.is_superuser or (created_invites < 3 and user.invites_left > 0):
        new_invite = Invitation.objects.create(inviter=user)
        if not user.is_superuser:
            user.invites_left -= 1
            user.save()
        invite_link = request.build_absolute_uri(
            reverse(
                'users:register_with_invite',
                kwargs={'invite_code': new_invite.code}
            )
        )

        previous_invitations = Invitation.objects.filter(inviter=user)
        previous_invitations_urls = [
            request.build_absolute_uri(
                reverse(
                    'users:register_with_invite',
                    kwargs={'invite_code': invite.code}
                )
            ) for invite in previous_invitations
        ]

        return render(request, 'invite_link.html', {
            'invite_link': invite_link,
            'previous_invitations': previous_invitations_urls
        })
    else:
        return render(
            request,
            'error.html', {'message': 'No invitations left.'}
        )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(
                request,
                'users/login.html',
                {'error': 'Invalid username or password.'}
            )
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


def handshake_count(code1, code2):
    parts1 = code1.split('-')
    parts2 = code2.split('-')

    common_base = 0
    while (
            common_base < min(len(parts1), len(parts2)) and
            parts1[common_base] == parts2[common_base]
    ):
        common_base += 1

    return (len(parts1) - common_base) + (len(parts2) - common_base)


@login_required
def follow_index(request):
    following_users = request.user.follower.all().values_list('author', flat=True)
    authors = CustomUser.objects.filter(id__in=following_users).annotate(
        offers_count=Count('offers'),
        transactions_count=Count('accepted_transactions')
    )

    context = {
        'following_users': authors,
    }

    return render(request, 'users/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(CustomUser, username=username)
    if author != request.user and not UserFollow.objects.filter(
        user=request.user, author=author
    ).exists():
        UserFollow.objects.create(user=request.user, author=author)
    return redirect("users:user_profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(CustomUser, username=username)
    if UserFollow.objects.filter(user=request.user, author=author).exists():
        UserFollow.objects.get(user=request.user, author=author).delete()
    return redirect("users:user_profile", username=username)


def user_profile(request, username):
    user_profile = get_object_or_404(CustomUser, username=username)
    is_following = False

    if request.user.is_authenticated:
        is_following = UserFollow.objects.filter(author=user_profile, user=request.user).exists()

    context = {
        'user_profile': user_profile,
        'is_following': is_following,
    }
    return render(request, 'users/profile.html', context)


def user_profile(request, username):
    user_profile = get_object_or_404(CustomUser, username=username)
    is_following = False

    if request.user.is_authenticated:
        is_following = UserFollow.objects.filter(author=user_profile, user=request.user).exists()

    inviter = user_profile.invited_by
    context = {
        'user_profile': user_profile,
        'is_following': is_following,
        'inviter': inviter,
    }
    return render(request, 'users/profile.html', context)
