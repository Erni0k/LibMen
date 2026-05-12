from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings

app_name = 'library'

urlpatterns = [
    # Public
    path('', views.book_list, name='book_list'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.LogoutPostView.as_view(), name='logout'),
    
    # User actions
    path('my-rentals/', views.my_rentals, name='my_rentals'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('my-fines/', views.my_fines, name='my_fines'),
    
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:loan_id>/', views.return_book, name='return_book'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('cancel-reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('pay-fine/<int:fine_id>/', views.pay_fine, name='pay_fine'),
    
    # Staff
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/loans/', views.staff_loans, name='staff_loans'),
    path('staff/reservations/', views.staff_reservations, name='staff_reservations'),
    path('staff/fines/', views.staff_fines, name='staff_fines'),
    path('staff/users/', views.staff_users, name='staff_users'),
    path('staff/books/', views.staff_books, name='staff_books'),
    path('staff/manage-books/', views.staff_manage_books, name='staff_manage_books'),
    path('staff/add-book/', views.staff_add_book, name='staff_add_book'),
    path('staff/add-book-copy/<int:book_id>/', views.staff_add_book_copy, name='staff_add_book_copy'),
    path('staff/delete-book-copy/<int:copy_id>/', views.staff_delete_book_copy, name='staff_delete_book_copy'),
    
    # Admin (under staff prefix to avoid conflict with Django's built-in admin)
    path('staff/admin/users/', views.admin_users, name='admin_users'),
    path('staff/admin/change-user-role/<int:user_id>/', views.admin_change_user_role, name='admin_change_user_role'),
    path('staff/admin/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('staff/admin/change-password/<int:user_id>/', views.admin_change_user_password, name='admin_change_user_password'),
]

# Test error pages in development mode
if settings.DEBUG:
    urlpatterns += [
        path('test-404/', views.handler404, name='test_404'),
        path('test-403/', views.handler403, name='test_403'),
    ]
