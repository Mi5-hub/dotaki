# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(verbose_name=_("Display name"), max_length=64)
    client_id = models.CharField(verbose_name=_("Dotaki Client ID"), max_length=32)
    language = models.IntegerField(verbose_name=_("Language"), default=1)
    additional_information = models.CharField(verbose_name=_("Additional information"), max_length=4096, blank=True, null=True)

    class Meta:
        ordering = ['display_name']

    def __str__(self):
        return f"{self.user.username}: {self.display_name} {self.client_id}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
