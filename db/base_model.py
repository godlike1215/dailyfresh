from django.db import models


class BaseModel(models.Model):
	# auto_now_add，创建的时候
	create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
	# auto_now，修改的时候
	update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
	is_delete = models.BooleanField(default=False, verbose_name='删除标记')

	class Meta:
		# 设置为抽象基类
		abstract = True
