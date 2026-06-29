from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = 'patient'
        ordering = ['name']

    def __str__(self):
        return self.name
