from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    WORKER = 'staff', 'Staff'
    USER = 'user', 'User'


class User(AbstractUser):
    role = models.CharField(max_length=50, choices=UserRole.choices, default=UserRole.USER)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username

class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    publication_year = models.IntegerField()
    publisher = models.CharField(max_length=100)
    cover_image_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.title

class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('available', 'Dostępna'),
        ('borrowed', 'Wypożyczona'),
        ('reserved', 'Zarezerwowana'),
        ('damaged', 'Uszkodzona'),
        ('lost', 'Zagubiona'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    shelf_location = models.CharField(max_length=50)
    acquisition_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.book.title} - {self.pk}"

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loans')
    loan_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    is_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.book_copy}"

    class Meta:
        permissions = [
            ('borrow_book', 'Can borrow book'),
            ('return_book', 'Can return book'),
        ]

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktywna'),
        ('fulfilled', 'Zrealizowana'),
        ('cancelled', 'Anulowana'),
        ('expired', 'Wygasła'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    class Meta:
        permissions = [
            ('reserve_book', 'Can reserve book'),
            ('cancel_reservation', 'Can cancel reservation'),
        ]

class Fine(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='fines')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fines')
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    issued_date = models.DateTimeField(auto_now_add=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Fine for {self.user.username}: {self.amount} PLN"

    class Meta:
        permissions = [
            ('pay_fine', 'Can pay fine'),
        ]