from django.contrib import admin
from .models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, Goods

# Register your models here.

admin.site.register(GoodsType)
admin.site.register(GoodsSKU)
admin.site.register(IndexTypeGoodsBanner)
admin.site.register(IndexPromotionBanner)
admin.site.register(IndexGoodsBanner)
admin.site.register(Goods)
