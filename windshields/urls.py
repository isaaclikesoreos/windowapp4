from django.urls import path
from .views import QuoteStartView

urlpatterns = [
    path('quote_start/', QuoteStartView.as_view(), name='quote_start'),
]
