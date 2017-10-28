from django.shortcuts import render
from django.http import HttpResponse
from rtmap.models import Router

from django.forms.models import model_to_dict
import json
import datetime  

# Create your views here.

  
class DateEncoder(json.JSONEncoder):  
    def default(self, obj):  
        if isinstance(obj, datetime.datetime):  
            return obj.strftime('%Y-%m-%d %H:%M:%S')  
        elif isinstance(obj, date):  
            return obj.strftime("%Y-%m-%d")  
        else:  
            return json.JSONEncoder.default(self, obj) 

def index(request):
    router_list = Router.objects.all().order_by('ip')
    context = {
            'router_list': router_list,
            }
    # 用locals() 返回 包含当前作用域所有变量的字典

    return render(request,'rtmap/list.html',context)


def map_view(request):
    router = Router.objects.all()
    router_list = [model_to_dict(r) for r in router]
    
    # 传给js  用json.dumps() &lt; Uncaught SyntaxError: Unexpected token &
    # datetime.datetime  is not JSON serializable 重写类方法
    context = {
                'router_list': [json.dumps(router_list, cls=DateEncoder)]
                }

    return render(request,'rtmap/map.html', context)

