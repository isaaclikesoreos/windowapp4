from django.apps import AppConfig


class WindshieldsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'windshields'


class AAdministrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_administration'
    verbose_name = 'Admin Console'