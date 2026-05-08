from django.contrib.auth.models import Group
from django.test import TestCase

from .models import User, UserRole


class RoleSyncTests(TestCase):
	def test_admin_role_gets_staff_and_group(self):
		user = User.objects.create_user(username='admin_user', password='pass12345', role=UserRole.ADMIN)

		self.assertTrue(user.is_staff)
		self.assertTrue(user.groups.filter(name=UserRole.ADMIN).exists())
		self.assertTrue(user.has_perm('library.delete_user'))
		self.assertTrue(user.has_perm('library.change_user'))

	def test_worker_role_gets_book_permissions(self):
		user = User.objects.create_user(username='worker_user', password='pass12345', role=UserRole.WORKER)

		self.assertTrue(user.is_staff)
		self.assertTrue(user.groups.filter(name='staff').exists())
		self.assertTrue(user.has_perm('library.add_book'))
		self.assertTrue(user.has_perm('library.change_book'))

	def test_unknown_role_is_normalized_to_user(self):
		user = User.objects.create_user(username='reader_user', password='pass12345', role='czytelnik')

		user.refresh_from_db()

		self.assertEqual(user.role, UserRole.USER)
		self.assertFalse(user.is_staff)
		self.assertTrue(user.groups.filter(name=UserRole.USER).exists())
		self.assertTrue(user.has_perm('library.borrow_book'))

