from django.http import HttpResponse
from django.shortcuts import render

def plans_home(request):
    return HttpResponse("<h1>Hello</h1>")