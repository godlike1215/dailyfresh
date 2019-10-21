from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from django.http import JsonResponse
from datetime import datetime
from apps.order.models import OrderGoods, OrderInfo
from django.db import transaction


# Create your views here.


class OrderPlaceView(View):
	def post(self, request):
		user = request.user
		cart_key = 'cart_%d' % user.id
		# getlist,获取符合条件的列表
		sku_ids = request.POST.getlist('sku_ids')
		conn = get_redis_connection('default')
		addrs = Address.objects.filter(user=user)
		total_count = 0
		total_amount = 0
		skus = []
		for sku_id in sku_ids:
			goods_sku = GoodsSKU.objects.get(id=sku_id)
			count = conn.hget(cart_key, sku_id)
			count = int(count.decode())
			if count > goods_sku.stock:
				return redirect(reverse('cart:main_cart'))
			goods_sku.count = count
			amount = goods_sku.price * count
			goods_sku.amount = amount
			skus.append(goods_sku)
			total_count += count
			total_amount += amount

		trans_expensive = 10
		total_pay = trans_expensive + total_amount
		sku_ids = ','.join(sku_ids)

		context = {
			'skus': skus,
			'total_count': total_count,
			'total_amount': total_amount,
			'total_pay': total_pay,
			'trans_expensive': trans_expensive,
			'addrs': addrs,
			'sku_ids': sku_ids,
		}

		return render(request, 'place_order.html', context)


class OrderCommitView(View):
	@transaction.atomic
	def post(self, request):
		user = request.user
		if not user.is_authenticated():
			return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
		# 获取addr_id pay_method,sku_ids
		addr_id = request.POST.get('addr_id')
		pay_method = request.POST.get('pay_method')
		sku_ids = request.POST.get('sku_ids')
		cart_key = 'cart_%d' % user.id

		if not all([addr_id, pay_method, sku_ids]):
			return JsonResponse({'res': 1, 'errmsg': '信息不全'})

		order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
		addr = Address.objects.get(id=addr_id)
		total_price = 0
		total_count = 0
		transit_price = 10
		# 设置事务保存点
		save_id = transaction.savepoint()
		order = OrderInfo.objects.create(
			order_id=order_id,
			user=user,
			addr=addr,
			pay_method=pay_method,
			total_count=total_count,
			total_price=total_price,
			transit_price=transit_price,
		)
		conn = get_redis_connection('default')

		sku_ids = sku_ids.split(',')
		for sku_id in sku_ids:
			goods_sku = GoodsSKU.objects.get(id=sku_id)
			count = conn.hget(cart_key, sku_id)
			count = int(count.decode())
			amount = goods_sku.price * count
			price = goods_sku.price
			if count > goods_sku.stock:
				# 如果库存不足回滚到保存点
				transaction.savepoint_rollback(save_id)
				return JsonResponse({'res': 3, 'errmsg': '库存不足'})
			order_goods = OrderGoods.objects.create(
				order=order,
				sku=goods_sku,
				count=count,
				price=price,
			)
			order_goods.save()
			# 更新销量和库存
			goods_sku.stock -= count
			goods_sku.sales += count
			goods_sku.save()
			# 计算总价格和商品总数
			total_count += count
			total_price += amount

		# 更新商品信息表中的总价格和商品总数量
		order.total_price = total_price
		order.total_count = total_count
		order.save()

		# 更新购物车信息
		conn.hdel(cart_key, *sku_ids)

		# 返回应答
		return JsonResponse({'res': 2, 'errmsg': '提交成功'})