"""
Admin class for the RegistrationProfile model, providing several
conveniences.
This is only enabled if 'registration' is in your INSTALLED_APPS
setting, which should only occur if you are using the model-based
activation workflow.
"""
from django.apps import apps
from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext_lazy as _

from .models import RegistrationProfile


class RegistrationAdmin(admin.ModelAdmin):
    actions = ['activate_users', 'resend_activation_email']
    list_display = ('user', 'activation_key_expired')
    raw_id_fields = ['user']
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

    def activate_users(self, request, queryset):
        """
        Activate the selected users, if they are not alrady
        activated.
        """
        for profile in queryset:
            RegistrationProfile.objects.activate_user(profile.activation_key)
    activate_users.short_description = _(u"Activate users")

    def resend_activation_email(self, request, queryset):
        """
        Re-send activation emails for the selected users.
        Note that this will *only* send activation emails for users
        who are eligible to activate; emails will not be sent to users
        whose activation keys have expired or who have already
        activated.
        """
        for profile in queryset:
            if not profile.activation_key_expired():
                profile.send_activation_email(
                    get_current_site(request)
                )
    resend_activation_email.short_description = _(u"Re-send activation emails")


if apps.is_installed('registration'):
    admin.site.register(RegistrationProfile, RegistrationAdmin)