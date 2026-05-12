from datetime import timedelta
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from library.models import Author, Book, BookCopy, Category, Fine, Loan, User


class Command(BaseCommand):
    help = 'Populate the database with example data'

    def handle(self, *args, **options):
        random.seed(42)

        def ensure_user(username, password, **defaults):
            user, created = User.objects.get_or_create(username=username, defaults=defaults)
            for field, value in defaults.items():
                setattr(user, field, value)
            user.set_password(password)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Użytkownik "{user.username}" został utworzony'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Użytkownik "{user.username}" już istnieje'))
            return user

        def ensure_book(isbn, title, author, category, description, publication_year, publisher, cover_image_url=''):
            book, created = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    'title': title,
                    'author': author,
                    'category': category,
                    'description': description,
                    'publication_year': publication_year,
                    'publisher': publisher,
                    'cover_image_url': cover_image_url,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Książka "{book.title}" została utworzona'))
            return book

        def ensure_copy(book, shelf_location, status='available'):
            copy, created = BookCopy.objects.get_or_create(
                book=book,
                shelf_location=shelf_location,
                defaults={'status': status},
            )
            if not created and copy.status != status:
                copy.status = status
                copy.save(update_fields=['status'])
            return copy

        def create_loan_with_optional_fine(user, copy, days_ago, due_in_days, is_returned, fine_amount=Decimal('0.00')):
            loan, created = Loan.objects.get_or_create(
                user=user,
                book_copy=copy,
                is_returned=is_returned,
                defaults={
                    'loan_date': timezone.now() - timedelta(days=days_ago),
                    'due_date': timezone.now() + timedelta(days=due_in_days),
                    'return_date': timezone.now() if is_returned else None,
                    'fine_amount': fine_amount,
                },
            )
            if created:
                copy.status = 'available' if is_returned else 'borrowed'
                copy.save(update_fields=['status'])
                self.stdout.write(self.style.SUCCESS(f'✓ Wypożyczenie utworzone: {user.username} -> {copy.book.title}'))

            if fine_amount > 0:
                fine, fine_created = Fine.objects.get_or_create(
                    loan=loan,
                    user=user,
                    defaults={
                        'amount': fine_amount,
                        'is_paid': False,
                    },
                )
                if not fine_created and (fine.amount != fine_amount or fine.is_paid):
                    fine.amount = fine_amount
                    fine.is_paid = False
                    fine.save(update_fields=['amount', 'is_paid'])
            return loan

        # Demo users
        primary_user = ensure_user(
            'jan_kowalski',
            'password123',
            email='jan.kowalski@example.com',
            first_name='Jan',
            last_name='Kowalski',
            role='user',
            is_active=True,
        )
        ensure_user(
            'anna_nowak',
            'password123',
            email='anna.nowak@example.com',
            first_name='Anna',
            last_name='Nowak',
            role='user',
            is_active=True,
        )
        ensure_user(
            'maria_staff',
            'password123',
            email='maria@library.pl',
            first_name='Maria',
            last_name='Kowalska',
            role='staff',
            is_staff=True,
            is_active=True,
        )
        ensure_user(
            'admin',
            'admin123',
            email='admin@library.pl',
            first_name='Admin',
            last_name='System',
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        # Create authors
        author1, _ = Author.objects.get_or_create(
            first_name='Fyodor',
            last_name='Dostoyevski',
            defaults={'biography': 'Rosyjski pisarz'}
        )
        author2, _ = Author.objects.get_or_create(
            first_name='Leo',
            last_name='Tolstoy',
            defaults={'biography': 'Rosyjski pisarz i filosof'}
        )

        extra_authors = []
        for first_name, last_name, biography in [
            ('Adam', 'Mickiewicz', 'Polski poeta romantyczny'),
            ('Bolesław', 'Prus', 'Polski powieściopisarz i publicysta'),
            ('Henryk', 'Sienkiewicz', 'Polski noblista i pisarz'),
            ('Olga', 'Tokarczuk', 'Polska pisarka i eseistka'),
            ('Stephen', 'King', 'Amerykański autor literatury grozy'),
            ('Agatha', 'Christie', 'Brytyjska pisarka kryminalna'),
            ('J.K.', 'Rowling', 'Brytyjska autorka literatury fantasy'),
            ('Isaac', 'Asimov', 'Autor science fiction i popularyzator nauki'),
        ]:
            author, _ = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'biography': biography},
            )
            extra_authors.append(author)

        # Create categories
        category1, _ = Category.objects.get_or_create(
            name='Klasyka',
            defaults={'description': 'Klasyczna literatura światowa'}
        )
        category2, _ = Category.objects.get_or_create(
            name='Dramat',
            defaults={'description': 'Dramaty i tragedii'}
        )

        extra_categories = []
        for name, description in [
            ('Kryminał', 'Powieści detektywistyczne i kryminalne'),
            ('Fantastyka', 'Literatura fantastyczna i science fiction'),
            ('Historia', 'Książki historyczne i biografie'),
            ('Romans', 'Powieści obyczajowe i romantyczne'),
            ('Przygodowa', 'Książki przygodowe i podróżnicze'),
        ]:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': description},
            )
            extra_categories.append(category)

        # Create books
        book1, _ = Book.objects.get_or_create(
            isbn='9788389550025',
            defaults={
                'title': 'Zbrodnia i kara',
                'author': author1,
                'category': category1,
                'description': 'Klasyczna powieść o psychologii zbrodni',
                'publication_year': 1866,
                'publisher': 'Wydawnictwo PWN',
                'cover_image_url': 'https://covers.openlibrary.org/b/id/1234567-M.jpg'
            }
        )
        book2, _ = Book.objects.get_or_create(
            isbn='9788389550087',
            defaults={
                'title': 'Wojna i pokój',
                'author': author2,
                'category': category1,
                'description': 'Epicka powieść o życiu w czasach wojen napoleońskich',
                'publication_year': 1869,
                'publisher': 'Wydawnictwo PWN',
                'cover_image_url': 'https://covers.openlibrary.org/b/id/2345678-M.jpg'
            }
        )

        demo_titles = [
            'Lalka', 'Faraon', 'Potop', 'Quo Vadis', 'W pustyni i w puszczy',
            'Kamienie na szaniec', 'Solaris', 'Cień wiatru', 'Imię róży', 'Złodziejka książek',
            'Rok 1984', 'Folwark zwierzęcy', 'Mistrz i Małgorzata', 'Proces', 'Przeminęło z wiatrem',
            'Duma i uprzedzenie', 'Wichrowe wzgórza', 'Zabić drozda', 'Król', 'Bastion',
            'Miasteczko Salem', 'Carrie', 'To', 'Kod Leonarda da Vinci', 'Inferno',
            'Anioły i demony', 'Opowieść podręcznej', 'Gra o tron', 'Dolina strachu', 'Sherlock Holmes',
            'Morderstwo w Orient Expressie', 'Dziesięciu Murzynków', 'Noc w bibliotece', 'Ostatnie życzenie', 'Krew elfów',
            'Czas pogardy', 'Chrzest ognia', 'Pani Jeziora', 'Diuna', 'Mesjasz Diuny',
            'Dzieci Diuny', 'Łowca androidów', 'Neuromancer', 'Fundacja', 'Druga Fundacja',
            'Dżuma', 'Mały Książę', 'Alchemik', 'Stary człowiek i morze', 'Moby Dick',
            'Wielki Gatsby', 'Wojna światów', 'Frankenstein', 'Dracula', 'Hobbit',
            'Władca Pierścieni', 'Powrót króla', 'Znak czterech', 'Biesy', 'Bracia Karamazow',
            'Idiota', 'Ania z Zielonego Wzgórza', 'Małe kobietki', 'Sapiens', 'Homo Deus',
            '21 lekcji na XXI wiek', 'Krótka historia czasu', 'Kosmos', 'Droga', 'Na wschód od Edenu',
            'Myszy i ludzie', 'Wyspa doktora Moreau', 'Człowiek w poszukiwaniu sensu', 'Medaliony', 'Mroczna wieża',
            'Zielona mila', 'Pachnidło', 'Gambit królowej', 'Czerwony smok', 'Milczenie owiec',
            'Niewidzialny człowiek', 'Atlas chmur', 'Zaginiona dziewczyna', 'Dziewczyna z pociągu', 'Gdzie śpiewają raki',
            'Północ i Południe', 'Ludzie bezdomni', 'Noce i dnie', 'Chłopi', 'Zemsta',
            'Kordian', 'Balladyna', 'Pan Tadeusz', 'Syzyfowe prace', 'Pamiętnik z powstania warszawskiego',
        ]

        demo_authors = [author1, author2] + extra_authors
        demo_categories = [category1, category2] + extra_categories

        books = [book1, book2]
        for index in range(1, 99):
            title = demo_titles[(index - 1) % len(demo_titles)]
            author = random.choice(demo_authors)
            category = random.choice(demo_categories)
            year = random.randint(1850, 2024)
            isbn = f'9787{index:09d}'
            book = ensure_book(
                isbn=isbn,
                title=f'{title} #{index:02d}',
                author=author,
                category=category,
                description=f'Demo książka: {title}',
                publication_year=year,
                publisher='Demo Wydawnictwo',
                cover_image_url=f'https://picsum.photos/seed/libmen-{index}/300/450',
            )
            books.append(book)

        # Create copies for all books
        for index, book in enumerate(books, start=1):
            ensure_copy(book, f'D-{index:03d}-1', 'available')
            ensure_copy(book, f'D-{index:03d}-2', 'available')

        # Create 15 demo borrower accounts with multiple loans and fines
        borrower_specs = [
            ('ola_kowalczyk', 'Ola', 'Kowalczyk'),
            ('piotr_wisniewski', 'Piotr', 'Wiśniewski'),
            ('ewa_zielinska', 'Ewa', 'Zielińska'),
            ('adam_wrobel', 'Adam', 'Wróbel'),
            ('karolina_kaczmarek', 'Karolina', 'Kaczmarek'),
            ('tomasz_klos', 'Tomasz', 'Kłos'),
            ('magda_pawlak', 'Magda', 'Pawlak'),
            ('lukasz_sadowski', 'Łukasz', 'Sadowski'),
            ('alicja_jablonska', 'Alicja', 'Jabłońska'),
            ('marcin_dabrowski', 'Marcin', 'Dąbrowski'),
            ('joanna_mazur', 'Joanna', 'Mazur'),
            ('jakub_krol', 'Jakub', 'Król'),
            ('malgorzata_lis', 'Małgorzata', 'Lis'),
            ('pawel_wojcik', 'Paweł', 'Wójcik'),
            ('natalia_baran', 'Natalia', 'Baran'),
        ]

        borrower_users = []
        for username, first_name, last_name in borrower_specs:
            borrower_users.append(
                ensure_user(
                    username,
                    'password123',
                    email=f'{username}@example.com',
                    first_name=first_name,
                    last_name=last_name,
                    role='user',
                    is_active=True,
                )
            )

        available_copies = list(BookCopy.objects.filter(status='available').order_by('id'))
        copy_cursor = 0
        for user_index, borrower in enumerate(borrower_users, start=1):
            if copy_cursor + 3 >= len(available_copies):
                break

            # returned overdue loan with fine
            returned_copy = available_copies[copy_cursor]
            copy_cursor += 1
            create_loan_with_optional_fine(
                borrower,
                returned_copy,
                days_ago=30 + user_index,
                due_in_days=-7,
                is_returned=True,
                fine_amount=Decimal(str(10 + (user_index % 5) * 5)),
            )

            # active loan with fine already due
            overdue_copy = available_copies[copy_cursor]
            copy_cursor += 1
            create_loan_with_optional_fine(
                borrower,
                overdue_copy,
                days_ago=15 + user_index,
                due_in_days=-2,
                is_returned=False,
                fine_amount=Decimal(str(5 + (user_index % 4) * 5)),
            )

            # active loan still in time
            active_copy = available_copies[copy_cursor]
            copy_cursor += 1
            create_loan_with_optional_fine(
                borrower,
                active_copy,
                days_ago=3 + user_index,
                due_in_days=12,
                is_returned=False,
                fine_amount=Decimal('0.00'),
            )

        # Ensure the sample loan for the primary demo user exists
        loan, created = Loan.objects.get_or_create(
            user=primary_user,
            book_copy=BookCopy.objects.get(book=book1, shelf_location='D-001-1'),
            is_returned=False,
            defaults={
                'loan_date': timezone.now(),
                'due_date': timezone.now() + timedelta(days=14),
                'fine_amount': Decimal('0.00'),
            }
        )
        if created:
            loan.book_copy.status = 'borrowed'
            loan.book_copy.save(update_fields=['status'])
            self.stdout.write(self.style.SUCCESS('✓ Przykładowe wypożyczenie zostało utworzone'))

        self.stdout.write(self.style.SUCCESS('\n✓ Baza danych została uzupełniona przykładowymi danymi!'))
        self.stdout.write('  - Książki demo: 100 łącznie (w tym istniejące i nowe)')
        self.stdout.write('  - Konta demo z wypożyczeniami: 15')
        self.stdout.write(f'  - Użytkownik bazowy: {primary_user.username} (hasło: password123)\n')
