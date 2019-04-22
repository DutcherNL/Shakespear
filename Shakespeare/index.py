from django.shortcuts import redirect


def index(request):
    return redirect('inquiries_overview')