from django.shortcuts import render
from django.http import HttpResponse
from rtmap.models import Router

# Create your views here.

def index(request):
    router_list = Router.objects.all().order_by('ip')
    context = {
            'router_list': router_list,
            }

    return render(request,'rtmap/list.html',context)


def map_view(request):

