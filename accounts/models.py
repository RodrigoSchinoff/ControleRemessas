
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class Organization(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    ROLE_CHOICES = [
        ("ORG_ADMIN", "Org Admin"),
        ("ORG_USER", "Org User"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="ORG_USER")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            # Garante no banco: no máximo 1 membership ativa por usuário
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="unique_active_membership_per_user",
            ),
        ]

    def __str__(self):
        status = "ativo" if self.is_active else "inativo"
        return f"{self.user.username} @ {self.organization.name} ({status})"

