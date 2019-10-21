from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time


# 创建Celery实例对象
app = Celery('celery_tasks.tasks', broker='redis://49.232.1.8:6379/1')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
	"""发送激活文件"""
	subject = '天天生鲜欢迎您'
	message = ''
	html_message = "<h1>%s您好，请通过此链接激活账户</h1>" \
				   "<a href='http://127.0.0.1:8000/user/active/%s'>http://127.0.0.1:8000/user/active/%s</a>" \
				   % (username, token, token)
	sender = settings.EMAIL_FROM
	receiver = [to_email]
	send_mail(subject, message, sender, receiver, html_message=html_message)
	time.sleep(5)