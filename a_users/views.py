from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import TemplateView, UpdateView, FormView, DeleteView
from django.contrib import messages
from .forms import CustomerForm, EmailForm, ChangeAvatarForm
from .models import Customer
import logging


logger = logging.getLogger(__name__)
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "a_users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user



        return context
    

    def post(self, request, *args, **kwargs):
        # Handle the avatar selection form submission
        selected_avatar = request.POST.get("selected_avatar")
        print(f"Selected avatar: {selected_avatar}")  # Debug log
        
        if selected_avatar:
            try:
                # Check if the selected_avatar value matches one of the choices
                valid_choices = [choice[0] for choice in Customer.AVATAR_CHOICES]
                if selected_avatar.split('/')[-1] in valid_choices:  # Extract file name from the path
                    # Update the user's profile with the new avatar
                    profile = request.user.profile
                    profile.selected_avatar = selected_avatar.split('/')[-1]  # Save only the file name
                    profile.save()
                    messages.success(request, "Your avatar has been updated successfully!")
                else:
                    messages.error(request, "Invalid avatar selection.")
            except Exception as e:
                print(f"Error updating avatar: {e}")  # Debug log
                messages.error(request, "An error occurred while updating your avatar.")
        else:
            messages.error(request, "Please select an avatar before saving.")

        return redirect("profile")  # Redirect back to the profile page




class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "a_users/profile_edit.html"

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["onboarding"] = self.request.path == reverse_lazy("profile-onboarding")
        return context

    def get_success_url(self):
        return reverse_lazy("profile")


class ProfileSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "a_users/profile_settings.html"


class ProfileEmailChangeView(LoginRequiredMixin, FormView):
    form_class = EmailForm
    template_name = "partials/email_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(id=self.request.user.id).exists():
            messages.warning(self.request, f"{email} is already in use.")
        else:
            form.save()
            send_email_confirmation(self.request, self.request.user)
            messages.success(self.request, "Email updated and confirmation sent.")
        return redirect("profile-settings")


class ProfileEmailVerifyView(LoginRequiredMixin, View):
    def get(self, request):
        send_email_confirmation(request, request.user)
        messages.success(request, "Verification email sent.")
        return redirect("profile-settings")


class ProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "a_users/profile_delete.html"
    success_url = reverse_lazy("home")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        logout(self.request)
        messages.success(self.request, "Account deleted successfully.")
        return super().form_valid(form)



