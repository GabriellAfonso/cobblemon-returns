from django.db import models


class DiscordPostedMessage(models.Model):
    ranking_id = models.CharField(max_length=32, unique=True)
    message_id = models.CharField(max_length=32)
    posted_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ranking_id']
        verbose_name = 'discord posted message'
        verbose_name_plural = 'discord posted messages'

    def __str__(self):
        return f"{self.ranking_id} → {self.message_id}"
