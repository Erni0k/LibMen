from django.shortcuts import render
from django.http import HttpResponseNotAllowed
from django.contrib.auth.views import LogoutView
from .models import Book


def book_list(request):
	books = Book.objects.select_related('author', 'category').all()
	return render(request, 'library/book_list.html', {'books': books})


class LogoutPostView(LogoutView):
	def get(self, request, *args, **kwargs):
		return HttpResponseNotAllowed(['POST'])
