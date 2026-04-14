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
