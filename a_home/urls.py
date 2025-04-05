from django.urls import path
from . import views
from .views import QuoteLookupFormView


urlpatterns = [
    path('', views.home, name='home'),  # Map '/home/' to the home view
    path('quote-lookup/', QuoteLookupFormView.as_view(), name='quote_lookup_form'),
    path('quote/<str:pin>/', views.quote_lookup_view, name='quote_lookup'),
    # Notification path
]