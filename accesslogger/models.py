from django.db import models

class Visit(models.Model):
    date = models.DateTimeField(editable=False)
    page = models.CharField(max_length=255)
    ip = models.CharField(max_length=20)
    ua = models.CharField(max_length=255)
    username = models.CharField(max_length=128)
    referrer = models.CharField(max_length=255)

    class Meta:
        ordering = ('-date',)

class VisitorCount(models.Model):
    day = models.DateField(editable=False)
    count = models.IntegerField(default=0)

    class Meta:
        ordering = ('-day',)

