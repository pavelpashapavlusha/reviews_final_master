from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    ROLES = (
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Administrator'),
    )
    role = models.CharField(
        max_length=256,
        choices=ROLES,
        default=ROLES[0][0],
    )
    bio = models.TextField(
        'Биография',
        blank=True,
    )
    email = models.EmailField(_('email address'), blank=False, unique=True)
    confirmation_code = models.IntegerField(
        _('confirmation_code'), blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR
