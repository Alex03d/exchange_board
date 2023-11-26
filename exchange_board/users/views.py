from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from logging_app.loguru_config import logger

from .forms import CustomUserCreationForm
from .models import CustomUser, EmailConfirmation, Invitation, UserFollow

from offers.models import Offer
from rating.models import Rating
from transactions.models import Transaction


def register(request, invite_code):
    logger.info(f"Начало регистрации пользователя с "
                f"пригласительным кодом {invite_code}")
    try:
        invitation = Invitation.objects.get(code=invite_code, used=False)
    except Invitation.DoesNotExist:
        logger.error(f"Ошибка регистрации: пригласительный код "
                     f"{invite_code} неверный или уже использован")
        return render(
            request,
            'users/error.html', {'message': 'Invalid or used invitation code.'}
        )
    logger.info(f"Пройдено начало регистрации пользователя с "
                f"пригласительным кодом {invite_code}")

    inviter = invitation.inviter
    logger.info(f"Запрошен пригласитель")
    if request.method == 'POST':
        logger.info(f"if request.method == 'POST'")
        form = CustomUserCreationForm(request.POST)
        logger.info(f"form = CustomUserCreationForm(request.POST)")
        if form.is_valid():
            logger.info(f"if form.is_valid():")
            user = form.save(commit=False)
            logger.info(f"user = form.save(commit=False)")
            user.email = form.cleaned_data['email']
            logger.info(f"user.email = form.cleaned_data['email']")
            user.invited_by = invitation.inviter
            logger.info(f"user.invited_by = invitation.inviter")
            user.invitation_code_used = invite_code
            logger.info(f"user.invitation_code_used = invite_code")

            next_sub_code = (
                    CustomUser.objects.filter(invited_by=inviter).count() + 1
            )
            logger.info(f"next_sub_code")
            user.referral_code = f"{inviter.referral_code}-{next_sub_code}"
            logger.info(f"user.referral_code {user.referral_code}")
            user.save()
            logger.info(f"user.save()")
            email_conf = EmailConfirmation(user=user)
            logger.info(f"email_conf")
            email_conf.save()
            logger.info(f"email_conf.save()")
            email_subject = "Complete Your Registration with Handshakes"
            email_body = f"""
            Hello {user.username},
            
            Thank you for signing up with Handshakes! We're excited to have 
            you join our community where you can connect, share, and engage 
            with others.

            To complete your registration and verify your email address, 
            please use the following confirmation code: 
            
            {email_conf.confirmation_code}

            Enter this code on the confirmation page to activate your account. 
            This verification helps to keep your account secure and ensures 
            that you can recover your account if you ever lose access.

            If you didn't sign up for Handshakes, you can safely ignore 
            this email.

            Welcome aboard,
            The Handshakes Team
            """
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            invitation.used = True
            invitation.invited_user = user
            invitation.save()
            if not inviter.is_superuser and inviter.invites_left > 0:
                inviter.invites_left -= 1
                inviter.save()
            return redirect('users:instructions')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


def confirm_email(request, token):
    logger.info(f"Попытка подтверждения email с токеном {token}")
    try:
        conf = EmailConfirmation.objects.get(
            confirmation_token=token,
            confirmed=False
        )
        conf.confirmed = True
        conf.user.is_email_confirmed = True
        conf.user.save()
        conf.save()
        return redirect('users:login')
    except EmailConfirmation.DoesNotExist:
        logger.error(f"Ошибка подтверждения email: неверная или "
                     f"использованная ссылка подтверждения {token}")
        return render(
            request,
            'users/error.html',
            {'message': 'Invalid or used confirmation link.'}
        )


def create_invite_page(request):
    user = request.user
    logger.info(f"Пользователь {user.username} создает страницу приглашения")
    previous_invitations = Invitation.objects.filter(inviter=user)
    previous_invitations_data = [
        (
            request.build_absolute_uri(
                reverse(
                    'users:register_with_invite',
                    kwargs={'invite_code': invite.code}
                )
            ),
            invite.invited_user
        ) for invite in previous_invitations
    ]

    has_invites = user.is_superuser or (
            Invitation.objects.filter(inviter=user).count() < 3
            and user.invites_left > 0)

    return render(request, 'users/invite_link.html', {
        'previous_invitations_data': previous_invitations_data,
        'has_invites': has_invites
    })


def generate_invite_link(request):
    user = request.user
    logger.info(f"Пользователь {user.username} генерирует "
                f"пригласительную ссылку")
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

        return JsonResponse({'invite_link': invite_link})
    else:
        logger.error(f"Пользователь {user.username} не может создать больше пригласительных ссылок")
        return JsonResponse({'error': 'No invitations left.'}, status=400)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        logger.info(f"Попытка входа в систему пользователя {username}")
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_email_confirmed or user.is_superuser:
                login(request, user)
                return redirect('index')
            else:
                confirm_email_code_url = reverse('users:confirm_email_code')
                return render(
                    request,
                    'users/login.html',
                    {
                        'error': 'Please confirm your email '
                                 'address before entering',
                                 'confirm_email_code_url':
                                     confirm_email_code_url
                    }
                )
        else:
            logger.error(f"Ошибка входа: неверное имя пользователя или "
                         f"пароль для {username}")
            return render(
                request,
                'users/login.html',
                {'error': 'Invalid username or password.'}
            )
    return render(request, 'users/login.html')


def logout_view(request):
    logger.info(f"Пользователь {request.user.username} выходит из системы")
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
    following_users = request.user.follower.all().values_list(
        'author',
        flat=True
    )
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
        is_following = UserFollow.objects.filter(
            author=user_profile,
            user=request.user
        ).exists()

    user_profile_code = user_profile.referral_code
    if request.user.is_authenticated:
        current_user_code = request.user.referral_code
    else:
        current_user_code = None

    handshakes = handshake_count(user_profile_code, current_user_code)
    inviter = user_profile.invited_by
    aggregated_rating = user_profile.aggregated_rating
    user_ratings = Rating.objects.filter(recipient=user_profile)

    author_offers = Offer.objects.filter(author=user_profile)
    author_transactions = Transaction.objects.filter(offer__in=author_offers)
    context = {
        'user_profile': user_profile,
        'is_following': is_following,
        'inviter': inviter,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),
        'aggregated_rating': aggregated_rating,
        'user_ratings': user_ratings,
        'author_transactions': author_transactions,
    }
    return render(request, 'users/profile.html', context)


def instructions_view(request):
    return render(request, 'users/instructions.html')


def resend_confirmation(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        logger.info(f"Попытка повторной отправки "
                    f"подтверждения на email {email}")
        try:
            user = CustomUser.objects.get(
                email=email,
                is_email_confirmed=False
            )
            email_confirmation = EmailConfirmation.objects.get(user=user)
            time_diff = timezone.now() - email_confirmation.timestamp

            if time_diff > timezone.timedelta(minutes=2):
                email_confirmation.timestamp = timezone.now()
                email_confirmation.save()

                send_mail(
                    f'Welcome to Handshakes. Confirm Your Email '
                    f'to Get Started. Your confirmation code: '
                    f'{email_confirmation.confirmation_code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                return render(
                    request,
                    'users/resend_confirmation_done.html',
                    {'message': 'A confirmation code has '
                                'been sent to your email.'}
                )
            else:
                return render(
                    request,
                    'users/resend_confirmation_wait.html',
                    {'message': 'You must wait at least 2 '
                                'minutes before requesting '
                                'a confirmation code again.'}
                )

        except CustomUser.DoesNotExist:
            logger.error(f"Пользователь с email {email} не "
                         f"найден или email уже подтвержден")
            return render(
                request,
                'users/resend_confirmation_no_exist_or_sent.html',
                {'message': 'Unable to find a user with that email '
                            'or the email has already been confirmed.'}
            )
        except EmailConfirmation.DoesNotExist:
            logger.error(f"Запрос на подтверждение {email} не "
                         f"найден.")
            return render(
                request,
                'users/confirmation_email_sent.html',
                {'message': 'No confirmation request '
                            'was found for this email.'}
            )
    else:
        return render(request, 'users/resend_confirmation.html')


def confirm_email_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        logger.info(f"Попытка подтверждения email с кодом {code}")
        try:
            email_conf = EmailConfirmation.objects.get(
                confirmation_code=code,
                confirmed=False
            )
            email_conf.confirmed = True
            email_conf.user.is_email_confirmed = True
            email_conf.user.save()
            email_conf.save()
            logger.info(f"Email успешно подтвержден с кодом {code}")
            return redirect('users:email_confirmed')
        except EmailConfirmation.DoesNotExist:
            logger.error(f"Неверный или уже использованный "
                         f"код подтверждения {code}")
            return render(
                request,
                'users/error.html',
                {'message': 'Invalid or used '
                            'confirmation code.'}
            )
    else:
        return render(request, 'users/confirm_email_code.html')


def email_confirmed(request):
    logger.info(f"Пользователь {request.user.username} подтвердил свой email")
    return render(request, 'users/email_confirmed.html')
