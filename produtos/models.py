from django.db import models
from accounts.models import Organization

class Produto(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("organization", "name"),)
        ordering = ("name",)

    def __str__(self):
        return self.name
