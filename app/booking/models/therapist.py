from django.db import models


class Therapist(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    speciality = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'therapist'
        ordering = ['name']

    def __str__(self):
        return self.name
