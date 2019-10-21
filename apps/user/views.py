from django.shortcuts import render, redirect, reverse
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU, GoodsType, IndexGoodsBanner, IndexPromotionBanner
from django.conf import settings
from celery_tasks.tasks import send_register_active_email
from apps.order.models import OrderGoods, OrderInfo
from django_redis import get_redis_connection
from utils.loginrequiredmixin import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import re

# Create your views here.


# def register(request):
# 	if request.method == 'POST':
# 		username = request.POST.get('user_name')
# 		password = request.POST.get('pwd')
# 		cpassword = request.POST.get('cpwd')
# 		email = request.POST.get('email')
# 		allow = request.POST.get('allow')
#
# 		if not all([username, password, email]):
# 			return render(request, 'register.html', {'errmsg': '信息没有填全'})
#
# 		try:
# 			user = User.objects.get(username=username)
# 			print(user)
# 		except User.DoesNotExist:
# 			user = None
# 		if user:
# 			return render(request, 'register.html', {'errmsg': '用户名已存在'})
#
# 		if password != cpassword:
# 			return render(request, 'register.html', {'errmsg': '密码不一致'})
#
# 		if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
# 			return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#
# 		if allow == 0:
# 			return render(request, 'register.html', {'errmsg': '请同意此协议'})
#
# 		user = User.objects.create_user(username, password, email)
# 		user.save()
# 		return redirect(reverse('goods:index'))
# 	else:
# 		return render(request, 'register.html')


class RegisterView(View):
	"""注册信息类"""
	def get(self, request):
		return render(request, 'register.html')

	def post(self, request):
		username = request.POST.get('user_name')
		password = request.POST.get('pwd')
		cpassword = request.POST.get('cpwd')
		email = request.POST.get('email')
		allow = request.POST.get('allow')

		if not all([username, password, email]):
			return render(request, 'register.html', {'errmsg': '信息没有填全'})

		try:
			user = User.objects.get(username=username)
		except User.DoesNotExist:
			user = None
		if user:
			return render(request, 'register.html', {'errmsg': '用户名已存在'})

		if password != cpassword:
			return render(request, 'register.html', {'errmsg': '密码不一致'})

		if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
			return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

		if allow == 'off':
			return render(request, 'register.html', {'errmsg': '请同意此协议'})

		user = User.objects.create_user(username=username, password=password, email=email)
		user.is_active = 0
		user.save()
		serializer = Serializer(settings.SECRET_KEY, 600)
		user_id = user.id
		confirm = {'user_id': user_id}
		token = serializer.dumps(confirm)
		token = token.decode()
		# subject = '天天生鲜欢迎您'
		# message = ''
		# html_message = "<h1>%s您好，请通过此链接激活账户</h1>" \
		# 		  "<a href='http://127.0.0.1:8000/user/active/%s'>http://127.0.0.1:8000/user/active/%s</a>" \
		# 		  %(username, token, token)
		# sender = settings.EMAIL_FROM
		# receiver = [email]
		# send_mail(subject, message, sender, receiver, html_message=html_message)
		# 使用delay（）函数可以把任务放入中间任务队列
		send_register_active_email.delay(email, username, token)
		return redirect(reverse('goods:index'))


class ActiveView(View):
	def get(self, request, token):
		serializer = Serializer(settings.SECRET_KEY, 600)
		info = serializer.loads(token)
		user_id = info['user_id']
		user = User.objects.get(id=user_id)
		user.is_active = 1
		user.save()
		return redirect('goods:index')


class LoginView(View):
	def get(self, request):
		if 'username' in request.COOKIES:
			username = request.COOKIES['username']
			checked = 'checked'
		else:
			username = ''
			checked = ''
		return render(request, 'login.html', {'username': username, 'checked': checked})

	def post(self, request):
		username = request.POST.get('username')
		password = request.POST.get('pwd')
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				next_url = request.GET.get('next', reverse('goods:index'))
				response = redirect(next_url)
				remember = request.POST.get('remember')
				if remember == 'on':
					response.set_cookie('username', username)
				else:
					response.delete_cookie('username')
				return response
			else:
				return render(request, 'login.html', {'errmsg': '用户未激活'})
		else:
			return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class UserInfoView(LoginRequiredMixin, View):
	def get(self, request):
		user = request.user
		address = Address.objects.get_address_is_default(user)

		# 连接redis
		# from redis import StrictRedis
		# StrictRedis(host='49.232.1.8', port=6379, db=1)

		conn = get_redis_connection('default')
		history_key = 'history_%s' % user.id

		# 获取用户浏览的最新的5个商品的id
		sku_ids = conn.lrange(history_key, 0, 4)
		sku_ids = [int(i.decode()) for i in sku_ids]
		print(sku_ids)
		goods_skus = GoodsSKU.objects.filter(id__in=sku_ids)
		sku_list = []
		# for goods_sku in goods_skus:
		# 	for sku_id in sku_ids:
		# 		if goods_sku.id == sku_id:
		# 			sku_list.append(sku_id)
		sku_list = [goods_sku for sku_id in sku_ids for goods_sku in goods_skus if goods_sku.id == sku_id]
		context = {
			'sku_list': sku_list,
			'page': 'info',
			'address': address,
			'good_skus': goods_skus,
		}
		return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
	def get(self, request):
		user = request.user
		order_infos = OrderInfo.objects.filter(user=user)
		context = {
			'order_infos': order_infos,
			'page': 'order',
		}
		return render(request, 'user_center_order.html', context)


class UserAddressView(LoginRequiredMixin, View):
	def get(self, request):
		user = request.user
		address = Address.objects.get_address_is_default(user)

		return render(request, 'user_center_site.html', {'page': 'active', 'address': address})

	def post(self, request):
		receiver = request.POST.get('receiver')
		addr = request.POST.get('address')
		zip_code = request.POST.get('zip_code')
		phone = request.POST.get('telephone')
		user = request.user

		if not all([receiver, addr, phone]):
			return render(request, 'user_center_site.html', {'errmsg': '信息不全'})

		address = Address.objects.get_address_is_default(user)
		if address:
			is_default = False
		else:
			is_default = True

		user_address = Address.objects.create(
			user=user,
			receiver=receiver,
			addr=addr,
			zip_code=zip_code,
			phone=phone,
			is_default=is_default
		)
		user_address.save()
		return redirect(reverse('user:user_center_site'))


class LogoutView(View):
	def get(self, request):
		logout(request)
		return redirect(reverse('goods:index'))


