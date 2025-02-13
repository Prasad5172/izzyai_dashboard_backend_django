from django.db import models
#     SubscriptionID (bigint)
# SubscriptionPrice (real) SubscriptionName (character varying)
# Create your models here.
class Subscriptions(models.Model) : 
    subscription_id = models.BigIntegerField(primary_key=True)
    subscription_price = models.FloatField()
    subscription_name = models.CharField(max_length=255)


    def __str__(self):
        return f"Subscription {self.subscription_id} - User {self.user_id}"