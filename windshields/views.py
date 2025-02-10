from django.shortcuts import render
from django.http import JsonResponse
from .forms import JobEntryForm
from .models import JobEntry
from django.views.generic.edit import FormView

class QuoteStartView(FormView):
    template_name = 'windshields/quote_start.html'
    form_class = JobEntryForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if request.is_ajax():
            if form.is_valid():
                job_entry = form.save()
                return JsonResponse({'success': True, 'job_entry_id': job_entry.id})
            else:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        else:
            # Fallback to default handling if not an AJAX request
            return super().post(request, *args, **kwargs)