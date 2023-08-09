from django.shortcuts import render


def index(request):
    template = 'offers/index.html'
    return render(request, template)
