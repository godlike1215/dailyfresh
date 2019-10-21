from django.conf.urls import url, include
from django.contrib import admin
from .views import AddView, CartView, CartUpdateView, CartDeleteView

urlpatterns = [
	url(r'^add$', AddView.as_view(), name='add'),
	url(r'^main_cart$', CartView.as_view(), name='main_cart'),
	url(r'^update$', CartUpdateView.as_view(), name='update'),
	url(r'^delete$', CartDeleteView.as_view(), name='delete'),
]
