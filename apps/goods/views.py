from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.core.paginator import Paginator, InvalidPage

# Create your views here.
from django_redis import get_redis_connection

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU, Goods
from apps.order.models import OrderGoods


class IndexView(View):
	def get(self, request):
		# 获取商品类型信息
		types = GoodsType.objects.all()

		# 获取轮播图片信息
		type_goods_banners = IndexGoodsBanner.objects.all()

		# 获取促销信息
		promotion_banners = IndexPromotionBanner.objects.all()

		# 获取分类商品信息
		for index_type in types:
			image_banners = IndexTypeGoodsBanner.objects.filter(type=index_type, display_type=1).order_by('index')
			title_banners = IndexTypeGoodsBanner.objects.filter(type=index_type, display_type=0).order_by('index')
			index_type.title_banners = title_banners
			index_type.image_banners = image_banners

		cart_count = 0
		user = request.user
		if user.is_authenticated():
			conn = get_redis_connection('default')
			cart_key = 'cart_%d' % user.id
			cart_count = conn.hlen(cart_key)

		context = {
			'types': types,
			'type_goods_banners': type_goods_banners,
			'promotion_banners': promotion_banners,
			'cart_count': cart_count,
		}

		return render(request, 'index.html', context)


class DetailView(View):
	def get(self, request, sku_id):
		user = request.user
		types = GoodsType.objects.all()
		order_goods = OrderGoods.objects.filter(id=sku_id).exclude(comment='')
		goods_sku = GoodsSKU.objects.get(id=sku_id)
		new_goods_skus = GoodsSKU.objects.all()[:2]
		# 获取这个种类的所有商品
		cart_count = 0
		same_spu_skus = GoodsSKU.objects.filter(goods=goods_sku.goods).exclude(id=sku_id)
		if user.is_authenticated():
			conn = get_redis_connection('default')
			history_key = 'history_%s' % user.id
			cart_key = 'cart_%d' % user.id
			conn.lrem(history_key, 0, sku_id)
			conn.lpush(history_key, sku_id)
			cart_count = conn.hlen(cart_key)

		context = {
			'types': types,
			'goods_sku': goods_sku,
			'new_goods_skus': new_goods_skus,
			'order_goods': order_goods,
			'same_spu_skus': same_spu_skus,
			'cart_count': cart_count,
		}
		return render(request, 'detail.html', context)


class ListView(View):
	def get(self, request, spu_id, page_num):
		goods_type = GoodsType.objects.get(id=spu_id)
		types = GoodsType.objects.all()
		sort = request.GET.get('sort')
		if sort == 'price':
			sku_goods = GoodsSKU.objects.filter(type=goods_type).order_by('price')
		elif sort == 'hot':
			sku_goods = GoodsSKU.objects.filter(type=goods_type).order_by('-price')
		else:
			sort = 'default'
			sku_goods = GoodsSKU.objects.filter(type=goods_type).order_by('-price')

		paginator = Paginator(sku_goods, 1)
		# try:
		page_con = paginator.page(page_num)
		num_pages = paginator.num_pages
		page_num = int(page_num)
		# except InvalidPage:
		# 	return redirect(reverse('goods:list 1 1'))
		if num_pages < 5:
			pages = range(1, num_pages+1)
		elif page_num <= 3:
			pages = range(1, 6)
		elif page_num > num_pages - 2:
			pages = range(num_pages-4, num_pages+1)
		else:
			pages = range(page_num-2, page_num+3)
		context = {
			'types': types,
			'sku_goods': sku_goods,
			'page_con': page_con,
			'paginator': paginator,
			'sort': sort,
			'pages': pages,
			'goods_type': goods_type,
		}
		return render(request, 'list.html', context)