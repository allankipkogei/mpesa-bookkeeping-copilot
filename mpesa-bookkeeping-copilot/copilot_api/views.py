from django.http import JsonResponse

def api_root(request):
    return JsonResponse({"message": "M-Pesa Bookkeeping API is running"})
