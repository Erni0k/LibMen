from django.shortcuts import render
from django.http import Http404
from django.core.exceptions import PermissionDenied


class ErrorPageMiddleware:
	"""Display custom error pages even in DEBUG mode"""
	
	def __init__(self, get_response):
		self.get_response = get_response
	
	def __call__(self, request):
		try:
			response = self.get_response(request)
			
			# Handle 404
			if response.status_code == 404:
				return render(request, 'library/404.html', status=404)
			
			# Handle 403
			if response.status_code == 403:
				return render(request, 'library/403.html', status=403)
			
			return response
		
		except Http404:
			return render(request, 'library/404.html', status=404)
		except PermissionDenied:
			return render(request, 'library/403.html', status=403)
		except Exception:
			raise
