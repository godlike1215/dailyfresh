from django.conf.urls import url, include
from django.contrib import admin
from .views import RegisterView, ActiveView, LoginView, UserInfoView, UserAddressView, UserOrderView, LogoutView

urlpatterns = [
	# url(r'^register', register, name='register'),
	url(r'^register/$', RegisterView.as_view(), name='register'),
	url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
	url(r'^login/', LoginView.as_view(), name='login'),
	url(r'^logout/', LogoutView.as_view(), name='logout'),
	url(r'^user-center-info/', UserInfoView.as_view(), name='user_center_info'),
	url(r'^user-center-order/', UserOrderView.as_view(), name='user_center_order'),
	url(r'^user-center-site/', UserAddressView.as_view(), name='user_center_site'),
]
