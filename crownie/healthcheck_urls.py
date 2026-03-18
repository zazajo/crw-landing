from django.urls import path
from django.http import HttpResponse

# This view is completely separate from your main app
def healthcheck(request):
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('health/', healthcheck, name='healthcheck'),
    path('', healthcheck),  # Also respond to root with 200
]