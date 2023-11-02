from django.db import models
from users.models import CustomUser


class Rating(models.Model):
    transaction = models.ForeignKey('transactions.Transaction', on_delete=models.CASCADE, related_name='ratings')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_ratings')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        from transactions.models import Transaction
        super(Rating, self).save(*args, **kwargs)
        self.update_user_rating(self.recipient)

    @staticmethod
    def update_user_rating(user):
        ratings = Rating.objects.filter(recipient=user)
        total_score = sum(rating.score for rating in ratings)
        user.aggregated_rating = total_score / ratings.count()
        user.save()
