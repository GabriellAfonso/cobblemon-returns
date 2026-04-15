from django.db import models


class CollectionLog(models.Model):
    STATUS_OK = 'ok'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [(STATUS_OK, 'OK'), (STATUS_ERROR, 'Error')]

    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.TextField(blank=True)
    players_updated = models.IntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'collection log'
        verbose_name_plural = 'collection logs'

    def __str__(self):
        return f'[{self.status.upper()}] {self.timestamp:%Y-%m-%d %H:%M} — {self.players_updated} players'
