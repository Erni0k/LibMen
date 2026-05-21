from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseNotAllowed, HttpResponseForbidden
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from .models import Book, BookCopy, Loan, Reservation, Fine, User, Author, Category


def is_staff(user):
	return user.is_staff or user.role == 'staff'

def is_admin(user):
	return user.is_staff and user.role == 'admin'


class LibraryUserCreationForm(UserCreationForm):
	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


def register(request):
	"""Register a new user"""
	if request.user.is_authenticated:
		return redirect('library:book_list')
	
	if request.method == 'POST':
		form = LibraryUserCreationForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			user.role = 'user'
			user.save()
			return redirect('library:login')
	else:
		form = LibraryUserCreationForm()
	
	return render(request, 'registration/register.html', {'form': form})


def book_list(request):
	"""Display all books with search and filter"""
	books = Book.objects.select_related('author', 'category').all()
	query = request.GET.get('search', '')
	category = request.GET.get('category', '')
	
	if query:
		books = books.filter(
			Q(title__icontains=query) | 
			Q(author__first_name__icontains=query) |
			Q(author__last_name__icontains=query) |
			Q(isbn__icontains=query)
		)
	
	if category:
		books = books.filter(category_id=category)
	
	# Get available copies count
	books = books.annotate(available_count=Count('copies', filter=Q(copies__status='available')))

	# Pagination
	page_size = 12
	paginator = Paginator(books, page_size)
	page_number = request.GET.get('page')
	books_page = paginator.get_page(page_number)

	context = {
		'books': books_page,
		'page_obj': books_page,
		'paginator': paginator,
		'categories': Category.objects.all(),
		'search_query': query,
		'selected_category': category,
	}
	return render(request, 'library/book_list.html', context)


def book_detail(request, book_id):
	"""Display book details"""
	book = get_object_or_404(Book, id=book_id)
	copies = book.copies.all()
	reservations = book.reservations.filter(status='active').count()
	
	user_reservation = None
	if request.user.is_authenticated:
		user_reservation = Reservation.objects.filter(
			user=request.user,
			book=book,
			status='active'
		).first()
	
	context = {
		'book': book,
		'copies': copies,
		'total_copies': copies.count(),
		'available_copies': copies.filter(status='available').count(),
		'active_reservations': reservations,
		'user_reservation': user_reservation,
	}
	return render(request, 'library/book_detail.html', context)


@login_required
def my_rentals(request):
	"""Display user's current and past rentals"""
	current_loans = Loan.objects.filter(
		user=request.user, 
		is_returned=False
	).select_related('book_copy__book__author').order_by('due_date')
	
	past_loans = Loan.objects.filter(
		user=request.user, 
		is_returned=True
	).select_related('book_copy__book__author').order_by('-return_date')[:10]
	
	# Check for overdue loans
	now = timezone.now()
	overdue_loans = current_loans.filter(due_date__lt=now)
	
	context = {
		'current_loans': current_loans,
		'past_loans': past_loans,
		'overdue_loans': overdue_loans,
	}
	return render(request, 'library/my_rentals.html', context)


@login_required
def my_reservations(request):
	"""Display user's reservations"""
	active_reservations = Reservation.objects.filter(
		user=request.user,
		status='active'
	).select_related('book__author').order_by('expiry_date')
	
	past_reservations = Reservation.objects.filter(
		user=request.user
	).exclude(status='active').select_related('book__author').order_by('-reservation_date')[:10]
	
	context = {
		'active_reservations': active_reservations,
		'past_reservations': past_reservations,
	}
	return render(request, 'library/my_reservations.html', context)


@login_required
def my_fines(request):
	"""Display user's fines"""
	unpaid_fines = Fine.objects.filter(user=request.user, is_paid=False).order_by('-issued_date')
	paid_fines = Fine.objects.filter(user=request.user, is_paid=True).order_by('-paid_date')[:10]
	total_unpaid = sum(fine.amount for fine in unpaid_fines)
	
	context = {
		'unpaid_fines': unpaid_fines,
		'paid_fines': paid_fines,
		'total_unpaid': total_unpaid,
	}
	return render(request, 'library/my_fines.html', context)


@login_required
def borrow_book(request, book_id):
	"""Borrow a book (create a new loan)"""
	book = get_object_or_404(Book, id=book_id)
	available_copy = book.copies.filter(status='available').first()
	
	if not available_copy:
		return render(request, 'library/error.html', {
			'error': f'Nie ma dostępnych kopii książki "{book.title}"'
		})
	
	due_date = timezone.now() + timedelta(days=14)
	loan = Loan.objects.create(
		user=request.user,
		book_copy=available_copy,
		due_date=due_date
	)
	
	available_copy.status = 'borrowed'
	available_copy.save()
	
	return redirect('library:my_rentals')


@user_passes_test(is_staff)
@require_http_methods(["POST"])
def return_book(request, loan_id):
	"""Return a borrowed book (staff/admin only). Staff can mark any loan as returned."""
	loan = get_object_or_404(Loan, id=loan_id, is_returned=False)

	loan.return_date = timezone.now()
	loan.is_returned = True

	# Calculate fine if overdue
	if loan.return_date > loan.due_date:
		days_overdue = (loan.return_date - loan.due_date).days
		fine_amount = days_overdue * 2.00  # 2 PLN per day
		loan.fine_amount = fine_amount

		# Create Fine record for the borrower
		Fine.objects.create(
			loan=loan,
			user=loan.user,
			amount=fine_amount
		)

	loan.save()
	loan.book_copy.status = 'available'
	loan.book_copy.save()

	return redirect('library:staff_loans')


@login_required
def reserve_book(request, book_id):
	"""Reserve a book"""
	book = get_object_or_404(Book, id=book_id)
	
	existing_reservation = Reservation.objects.filter(
		user=request.user,
		book=book,
		status='active'
	).first()
	
	if existing_reservation:
		return render(request, 'library/error.html', {
			'error': 'Już zarezerwowałeś tę książkę'
		})
	
	expiry_date = timezone.now() + timedelta(days=30)
	Reservation.objects.create(
		user=request.user,
		book=book,
		expiry_date=expiry_date
	)
	
	return redirect('library:my_reservations')


@login_required
def cancel_reservation(request, reservation_id):
	"""Cancel a reservation"""
	reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
	
	reservation.status = 'cancelled'
	reservation.save()
	
	return redirect('library:my_reservations')


@login_required
def pay_fine(request, fine_id):
	"""Mark fine as paid"""
	fine = get_object_or_404(Fine, id=fine_id, user=request.user)
	
	if request.method == 'POST':
		fine.is_paid = True
		fine.paid_date = timezone.now()
		fine.save()
		return redirect('library:my_fines')
	
	return render(request, 'library/pay_fine.html', {'fine': fine})


# Staff/Admin Views
@user_passes_test(is_staff)
def staff_dashboard(request):
	"""Staff dashboard with library statistics"""
	stats = {
		'total_books': Book.objects.count(),
		'total_copies': BookCopy.objects.count(),
		'available_copies': BookCopy.objects.filter(status='available').count(),
		'borrowed_copies': BookCopy.objects.filter(status='borrowed').count(),
		'active_loans': Loan.objects.filter(is_returned=False).count(),
		'overdue_loans': Loan.objects.filter(is_returned=False, due_date__lt=timezone.now()).count(),
		'active_reservations': Reservation.objects.filter(status='active').count(),
		'unpaid_fines': Fine.objects.filter(is_paid=False).count(),
		'total_unpaid_fines': sum(f.amount for f in Fine.objects.filter(is_paid=False)),
	}
	
	recent_loans = Loan.objects.select_related('user', 'book_copy__book').order_by('-loan_date')[:10]
	overdue_loans = Loan.objects.filter(is_returned=False, due_date__lt=timezone.now()).select_related('user', 'book_copy__book').order_by('due_date')
	
	context = {
		'stats': stats,
		'recent_loans': recent_loans,
		'overdue_loans': overdue_loans,
	}
	return render(request, 'library/staff/dashboard.html', context)


@user_passes_test(is_staff)
def staff_loans(request):
	"""Manage all loans"""
	loans = Loan.objects.select_related('user', 'book_copy__book__author').order_by('-loan_date')
	filter_type = request.GET.get('filter', 'all')
	
	if filter_type == 'active':
		loans = loans.filter(is_returned=False)
	elif filter_type == 'overdue':
		loans = loans.filter(is_returned=False, due_date__lt=timezone.now())
	elif filter_type == 'returned':
		loans = loans.filter(is_returned=True)
	
	context = {
		'loans': loans,
		'filter': filter_type,
	}
	return render(request, 'library/staff/loans.html', context)


@user_passes_test(is_staff)
def staff_reservations(request):
	"""Manage all reservations"""
	reservations = Reservation.objects.select_related('user', 'book__author').order_by('expiry_date')
	filter_type = request.GET.get('filter', 'active')
	
	if filter_type == 'all':
		pass
	else:
		reservations = reservations.filter(status=filter_type)
	
	context = {
		'reservations': reservations,
		'filter': filter_type,
	}
	return render(request, 'library/staff/reservations.html', context)


@user_passes_test(is_staff)
def staff_fines(request):
	"""Manage all fines"""
	fines = Fine.objects.select_related('user', 'loan__book_copy__book').order_by('-issued_date')
	filter_type = request.GET.get('filter', 'unpaid')
	
	if filter_type == 'unpaid':
		fines = fines.filter(is_paid=False)
	elif filter_type == 'paid':
		fines = fines.filter(is_paid=True)
	
	context = {
		'fines': fines,
		'filter': filter_type,
		'total': sum(f.amount for f in fines),
	}
	return render(request, 'library/staff/fines.html', context)


@user_passes_test(is_staff)
def staff_users(request):
	"""Manage users"""
	users = User.objects.annotate(
		total_loans=Count('loans'),
		active_loans=Count('loans', filter=Q(loans__is_returned=False)),
		unpaid_fines=Count('fines', filter=Q(fines__is_paid=False))
	).order_by('-date_joined')
	
	context = {
		'users': users,
	}
	return render(request, 'library/staff/users.html', context)


@user_passes_test(is_staff)
def staff_books(request):
	"""Manage books"""
	books = Book.objects.select_related('author', 'category').annotate(
		total_copies=Count('copies'),
		available_copies=Count('copies', filter=Q(copies__status='available')),
		reservations=Count('reservations', filter=Q(reservations__status='active'))
	).order_by('-id')
	
	context = {
		'books': books,
	}
	return render(request, 'library/staff/books.html', context)


# Admin Views
@user_passes_test(is_admin)
def admin_users(request):
	"""Manage users - change roles and delete"""
	users = User.objects.annotate(
		total_loans=Count('loans'),
		active_loans=Count('loans', filter=Q(loans__is_returned=False)),
		total_fines=Count('fines', filter=Q(fines__is_paid=False))
	).order_by('-date_joined')
	
	context = {'users': users}
	return render(request, 'library/admin/users.html', context)


@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_change_user_role(request, user_id):
	"""Change user role"""
	user = get_object_or_404(User, id=user_id)
	if user == request.user:
		return HttpResponseForbidden("Nie możesz zmienić swoją rolę")
	
	new_role = request.POST.get('role')
	if new_role in dict(User._meta.get_field('role').choices):
		user.role = new_role
		if new_role == 'admin':
			user.is_staff = True
		elif new_role == 'staff':
			user.is_staff = True
		else:
			user.is_staff = False
		user.save()
	
	return redirect('library:admin_users')


@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_delete_user(request, user_id):
	"""Delete a user"""
	user = get_object_or_404(User, id=user_id)
	if user == request.user:
		return HttpResponseForbidden("Nie możesz usunąć siebie")
	
	user.delete()
	return redirect('library:admin_users')


@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_change_user_password(request, user_id):
	"""Change user password"""
	user = get_object_or_404(User, id=user_id)
	if user == request.user:
		return HttpResponseForbidden("Nie możesz zmienić swoje hasło tutaj")
	
	new_password = request.POST.get('new_password')
	if new_password:
		user.set_password(new_password)
		user.save()
	
	return redirect('library:admin_users')


@user_passes_test(is_staff)
def staff_manage_books(request):
	"""Manage books - add, edit, delete"""
	books = Book.objects.select_related('author', 'category').prefetch_related('copies').annotate(
		total_copies=Count('copies'),
		available_copies=Count('copies', filter=Q(copies__status='available')),
		borrowed_copies=Count('copies', filter=Q(copies__status='borrowed')),
		reserved_copies=Count('copies', filter=Q(copies__status='reserved')),
	)
	authors = Author.objects.all()
	categories = Category.objects.all()
	
	context = {
		'books': books,
		'authors': authors,
		'categories': categories,
	}
	return render(request, 'library/staff/manage_books.html', context)


@user_passes_test(is_staff)
@require_http_methods(["POST"])
def staff_add_book(request):
	"""Add a new book"""
	try:
		title = request.POST.get('title')
		isbn = request.POST.get('isbn')
		author_id = request.POST.get('author')
		author_first_name = (request.POST.get('author_first_name') or '').strip()
		author_last_name = (request.POST.get('author_last_name') or '').strip()
		author_biography = (request.POST.get('author_biography') or '').strip()
		category_id = request.POST.get('category')
		category_name = (request.POST.get('category_name') or '').strip()
		category_description = (request.POST.get('category_description') or '').strip()
		description = request.POST.get('description')
		cover_image_url = (request.POST.get('cover_image_url') or '').strip()
		publication_year = request.POST.get('publication_year')
		publisher = request.POST.get('publisher')
		
		if author_first_name and author_last_name:
			author = Author.objects.create(
				first_name=author_first_name,
				last_name=author_last_name,
				biography=author_biography,
			)
		elif author_id:
			author = Author.objects.get(id=author_id)
		else:
			raise ValueError('Wybierz istniejącego autora albo dodaj nowego.')

		if category_name:
			category, _ = Category.objects.get_or_create(
				name=category_name,
				defaults={'description': category_description},
			)
			if category_description and not category.description:
				category.description = category_description
				category.save(update_fields=['description'])
		elif category_id:
			category = Category.objects.get(id=category_id)
		else:
			raise ValueError('Wybierz istniejącą kategorię albo dodaj nową.')
		
		book = Book.objects.create(
			title=title,
			isbn=isbn,
			author=author,
			category=category,
			description=description,
			cover_image_url=cover_image_url or None,
			publication_year=publication_year,
			publisher=publisher
		)
		return redirect('library:staff_manage_books')
	except Exception as e:
		return render(request, 'library/error.html', {'error': str(e)})


@user_passes_test(is_staff)
@require_http_methods(["POST"])
def staff_add_book_copy(request, book_id):
	"""Add a new copy of a book"""
	try:
		book = get_object_or_404(Book, id=book_id)
		shelf_location = request.POST.get('shelf_location')
		quantity = int(request.POST.get('quantity', 1))
		
		for i in range(quantity):
			BookCopy.objects.create(
				book=book,
				shelf_location=f"{shelf_location}-{i+1}"
			)
		return redirect('library:staff_manage_books')
	except Exception as e:
		return render(request, 'library/error.html', {'error': str(e)})


@user_passes_test(is_staff)
@require_http_methods(["POST"])
def staff_delete_book_copy(request, copy_id):
	"""Delete a book copy"""
	copy = get_object_or_404(BookCopy, id=copy_id)
	if copy.status != 'available':
		return render(request, 'library/error.html', {
			'error': 'Można usunąć tylko dostępne kopie'
		})
	copy.delete()
	return redirect('library:staff_manage_books')


class LogoutPostView(LogoutView):
	def get(self, request, *args, **kwargs):
		return HttpResponseNotAllowed(['POST'])


def handler404(request, exception=None):
	"""Handle 404 errors"""
	return render(request, 'library/404.html', status=404)


def handler403(request, exception=None):
	"""Handle 403 errors"""
	return render(request, 'library/403.html', status=403)
