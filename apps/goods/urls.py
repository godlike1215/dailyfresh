from django.conf.urls import url
from . import views
from apps.goods.views import DetailView, ListView

urlpatterns = [
	url(r'^$', views.IndexView.as_view(), name='index'),
	url(r'^detail/(?P<sku_id>\d+)$', DetailView.as_view(), name='detail'),
	url(r'^list/(?P<spu_id>\d+)/(?P<page_num>\d+)$', ListView.as_view(), name='list'),
]
