from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Author, Category, Book, BookCopy, Loan, Reservation, Fine

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )  # type: ignore[assignment]

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        fieldsets.append(('Role', {'fields': ('role',)}))
        return fieldsets

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'publication_year', 'isbn')
    list_filter = ('category', 'publication_year')
    search_fields = ('title', 'isbn', 'author__first_name', 'author__last_name')

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'status', 'shelf_location')
    list_filter = ('status',)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'book_copy', 'loan_date', 'due_date', 'is_returned')
    list_filter = ('is_returned', 'loan_date')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reservation_date', 'expiry_date', 'status')
    list_filter = ('status',)

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'is_paid', 'issued_date')
    list_filter = ('is_paid',)