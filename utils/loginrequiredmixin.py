from django.contrib.auth.decorators import login_required


class LoginRequiredMixin:
	@classmethod
	def as_view(cls, **initkwargs):
		view = super().as_view(**initkwargs)
		return login_required(view)
