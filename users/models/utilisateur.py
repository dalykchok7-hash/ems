from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Utilisateur(AbstractUser):

    ROLE_CHOICES = [
        ('admin',     'Admin'),
        ('personnel', 'Personnel'),
    ]

    SHIFT_CHOICES = [
        ('jour', 'Jour'),
        ('soir', 'Soir'),
    ]

    # ── Clé primaire ─────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ── Champs ───────────────────────────────
    cin = models.CharField(
        max_length=20,
        unique=True
    )

    telephone = models.CharField(
        max_length=20,
        blank=True,
        default=''
    )

    photo = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='personnel'
    )
    reset_token = models.CharField(
        max_length=255, 
        null=True, 
        blank=True)

    shift = models.CharField(
        max_length=10,
        choices=SHIFT_CHOICES,
        blank=True,
        default=''
    )

    date_embauche = models.DateField(
        null=True,
        blank=True
    )
    email = models.EmailField(
    unique=True
)

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email', 'role']

    class Meta:
        verbose_name        = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_personnel(self):
        return self.role == 'personnel'