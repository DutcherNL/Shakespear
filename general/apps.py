from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig

from django.db.models.signals import pre_migrate, post_migrate


class PermissionUpdatingMixin:
    # A mixin that updates the User permission models for this specific app.

    # Permissions in tuple format (code, verbose)
    permissions = [
    ]

    def update_permissions(self, **kwargs):
        # Load the models here, as they are not yet loaded upon initialisation
        from django.contrib.auth.models import Permission, User
        from django.contrib.contenttypes.models import ContentType

        User_ct = ContentType.objects.get_for_model(User)

        for permission in self.permissions:
            if not Permission.objects.filter(
                    codename=permission[0],
                    content_type=User_ct,
            ).exists():
                Permission.objects.create(
                    codename=permission[0],
                    name=permission[1],
                    content_type=User_ct,
                )

    def ready(self):
        super(PermissionUpdatingMixin, self).ready()
        post_migrate.connect(self.update_permissions, sender=self)


class ShakespeareGeneralConfig(AppConfig):
    name = 'general'


class MyAdminConfig(AdminConfig):
    default_site = 'Shakespeare.admin.MyAdminSite'
