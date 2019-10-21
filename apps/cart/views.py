from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from utils.loginrequiredmixin import LoginRequiredMixin

# Create your views here.


class AddView(View):
	def post(self, request):
		user = request.user
		sku_id = request.POST.get('sku_id')
		count = request.POST.get('count')
		count = int(count)
		goods_sku = GoodsSKU.objects.get(id=sku_id)

		if not user.is_authenticated():
			return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
		# 校验数据完整性
		if not all([sku_id, count]):
			return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

		conn = get_redis_connection('default')
		cart_key = 'cart_%d' % user.id
		cart_count = conn.hget(cart_key, sku_id)
		if cart_count:
			cart_count = int(cart_count.decode())
			count += cart_count
			if count > goods_sku.stock:
				return JsonResponse({'res': 2, 'errmsg': '库存不足'})
		conn.hset(cart_key, sku_id, count)
		total_count = conn.hlen(cart_key)
		return JsonResponse({'res': 3, 'total_count': total_count, 'errmsg': '添加成功'})


class CartView(LoginRequiredMixin, View):
	def get(self, request):
		conn = get_redis_connection('default')
		user = request.user
		cart_key = 'cart_%d' % user.id
		cart_dict = conn.hgetall(cart_key)
		total_price = 0
		total_count = 0
		sku_list = []
		for sku_id, count in cart_dict.items():
			sku_id = sku_id.decode()
			goods_sku = GoodsSKU.objects.get(id=sku_id)
			count = int(count.decode())
			goods_sku.count = count
			amount = goods_sku.price * count
			goods_sku.amount = amount
			sku_list.append(goods_sku)
			total_count += count
			total_price += amount

		context = {
			'total_price': total_price,
			'total_count': total_count,
			'sku_list': sku_list,
		}
		return render(request, 'cart.html', context)


class CartUpdateView(View):
	def post(self, request):
		user = request.user
		sku_id = request.POST.get('sku_id')
		count = request.POST.get('count')
		sku = GoodsSKU.objects.get(id=sku_id)

		if not user.is_authenticated():
			return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
		# 校验数据完整性
		if not all([sku_id, count]):
			return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
		if int(count) > sku.stock:
			return JsonResponse({'res': 2, 'errmsg': '库存不足'})

		conn = get_redis_connection('default')
		cart_key = 'cart_%d' % user.id
		conn.hset(cart_key, sku_id, count)
		return JsonResponse({'res': 3, 'errmsg': '更新成功', 'sku_id': sku_id, 'count': count})


class CartDeleteView(View):
	def post(self, request):
		user = request.user
		sku_id = request.POST.get('sku_id')
		cart_key = 'cart_%d' % user.id
		if not user.is_authenticated():
			return JsonResponse({'res': 0, 'errmsg': '未登录'})

		if not sku_id:
			return JsonResponse({'res': 1, 'errmsg': '商品不存在'})

		conn = get_redis_connection('default')
		conn.hdel(cart_key, sku_id)
		return JsonResponse({'res': 2, 'errmsg': '删除成功'})
