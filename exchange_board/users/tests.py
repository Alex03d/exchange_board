from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, Invitation, UserFollow
from .views import handshake_count


class CustomUserModelTestCase(TestCase):

    def test_superuser_referral_code_creation(self):
        user = CustomUser.objects.create_superuser(
            username="superuser",
            email="superuser@example.com",
            password="testpassword123")
        self.assertEqual(user.referral_code, "1")


class RegistrationViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.inviter = CustomUser.objects.create_user(
            username="inviter",
            password="testpassword123"
        )
        self.invitation = Invitation.objects.create(inviter=self.inviter)
        self.valid_register_url = reverse(
            'users:register_with_invite',
            args=[str(self.invitation.code)]
        )
        self.invalid_register_url = reverse(
            'users:register_with_invite',
            args=["00000000-0000-0000-0000-000000000000"]
        )

    def test_valid_invitation_registration(self):
        response = self.client.post(self.valid_register_url, {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_invitation_registration(self):
        response = self.client.post(self.invalid_register_url, {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        self.assertContains(response, 'Invalid or used invitation code.')


class LoginLogoutViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword123"
        )
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')

    def test_valid_login(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertContains(response, 'Invalid username or password.')


class InviteViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword123"
        )
        self.superuser = CustomUser.objects.create_superuser(
            username="superuser",
            email="superuser@example.com",
            password="testpassword123"
        )
        self.create_invite_url = reverse('users:create_invite')

    def test_superuser_create_invite(self):
        self.client.login(username="superuser", password="testpassword123")
        response = self.client.get(self.create_invite_url)
        self.assertEqual(response.status_code, 200)
        # Maybe check for certain elements in the returned context

    def test_regular_user_create_invite(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.create_invite_url)
        self.assertEqual(response.status_code, 200)
        # Maybe check for certain elements in the returned context

    def test_no_invites_left(self):
        # Set the user invites to zero
        self.user.invites_left = 0
        self.user.save()

        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.create_invite_url)
        self.assertContains(response, 'No invitations left.')


class HandshakeCountTestCase(TestCase):

    def test_handshake_count(self):
        count = handshake_count("1-2", "1-2-3")
        self.assertEqual(count, 1)

        count = handshake_count("1-2", "1-4")
        self.assertEqual(count, 2)
        # Add more test cases as required.


class FollowViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user1 = CustomUser.objects.create_user(
            username="user1",
            password="testpassword123"
        )
        self.user2 = CustomUser.objects.create_user(
            username="user2",
            password="testpassword123"
        )
        self.follow_index_url = reverse('users:follow_index')
        self.follow_url = reverse('users:profile_follow', args=['user2'])
        self.unfollow_url = reverse('users:profile_unfollow', args=['user2'])

    def test_follow_index(self):
        self.client.login(username="user1", password="testpassword123")
        response = self.client.get(self.follow_index_url)
        self.assertEqual(response.status_code, 200)

    def test_profile_follow(self):
        self.client.login(username="user1", password="testpassword123")
        response = self.client.get(self.follow_url)
        self.assertEqual(response.status_code, 302)
        # Assert that user1 now follows user2
        self.assertTrue(UserFollow.objects.filter(user=self.user1, author=self.user2).exists())

    def test_profile_unfollow(self):
        UserFollow.objects.create(user=self.user1, author=self.user2)

        self.client.login(username="user1", password="testpassword123")
        response = self.client.get(self.unfollow_url)
        self.assertEqual(response.status_code, 302)
        # Assert that user1 no longer follows user2
        self.assertFalse(UserFollow.objects.filter(user=self.user1, author=self.user2).exists())


class UserProfileViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword123"
        )
        self.profile_url = reverse('users:user_profile', args=['testuser'])

    def test_user_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        # Maybe check for certain elements in the returned context, e.g.:
        self.assertContains(response, 'testuser')


class RegisterViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.inviter = CustomUser.objects.create_user(
            username="inviter",
            password="testpassword123",
            invites_left=5
        )
        self.invitation = Invitation.objects.create(inviter=self.inviter)
        self.register_url = reverse(
            'users:register_with_invite',
            args=[str(self.invitation.code)]
        )

    def test_successful_registration(self):
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            CustomUser.objects.filter(username='testuser').exists()
        )
        self.inviter.refresh_from_db()
        self.assertEqual(self.inviter.invites_left, 4)

    def test_invalid_form_registration(self):
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword124',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            CustomUser.objects.filter(username='testuser').exists()
        )


class CreateInviteViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword123",
            invites_left=1
        )
        self.superuser = CustomUser.objects.create_superuser(
            username="superuser",
            password="testpassword123",
            email="superuser@example.com"
        )
        self.create_invite_url = reverse('users:create_invite')

    def test_create_invite(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.create_invite_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invitation.objects.count(), 1)

    def test_create_invite_no_invites_left(self):
        self.user.invites_left = 0
        self.user.save()
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.create_invite_url)
        self.assertContains(response, 'No invitations left.')

    def test_superuser_create_invite(self):
        self.client.login(username="superuser", password="testpassword123")
        response = self.client.get(self.create_invite_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invitation.objects.count(), 1)


class LoginViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword123"
        )
        self.login_url = reverse('users:login')

    def test_already_logged_in_user(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)


class LogoutViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword123"
        )
        self.logout_url = reverse('users:logout')

    def test_logout(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
