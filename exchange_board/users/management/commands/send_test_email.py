from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sends a test email."

    def handle(self, *args, **kwargs):
        send_mail(
            'Test Email',
            'This is a test email.',
            settings.DEFAULT_FROM_EMAIL,
            ['adondokov@gmail.com'],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS('Successfully sent test email!'))
