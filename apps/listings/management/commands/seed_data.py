from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import User
from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.reviews.models import Review


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными: пользователи, объявления, бронирования, отзывы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все существующие тестовые данные перед созданием новых',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очищаем старые данные...')
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Listing.all_objects.all().delete()
            User.objects.filter(email__endswith='@seed.test').delete()

        with transaction.atomic():
            landlords = self._create_landlords()
            tenants = self._create_tenants()
            listings = self._create_listings(landlords)
            bookings = self._create_bookings(tenants, listings)
            self._create_reviews(bookings)

        self.stdout.write(self.style.SUCCESS('Готово! База заполнена тестовыми данными.'))
        self.stdout.write('')
        self.stdout.write('Тестовые аккаунты (пароль у всех: testpass123):')
        self.stdout.write('  Арендодатель: anna@seed.test')
        self.stdout.write('  Арендодатель: max@seed.test')
        self.stdout.write('  Арендатор:    ivan@seed.test')
        self.stdout.write('  Арендатор:    olga@seed.test')

    def _create_landlords(self):
        data = [
            ('anna@seed.test', 'anna_landlord', '+491234567890'),
            ('max@seed.test', 'max_landlord', '+491234567891'),
        ]
        users = []
        for email, username, phone in data:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={'username': username, 'phone': phone, 'role': User.Role.LANDLORD}
            )
            user.set_password('testpass123')
            user.role = User.Role.LANDLORD
            user.save()
            users.append(user)
        self.stdout.write(f'Создано арендодателей: {len(users)}')
        return users

    def _create_tenants(self):
        data = [
            ('ivan@seed.test', 'ivan_tenant'),
            ('olga@seed.test', 'olga_tenant'),
        ]
        users = []
        for email, username in data:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={'username': username, 'role': User.Role.TENANT}
            )
            user.set_password('testpass123')
            user.role = User.Role.TENANT
            user.save()
            users.append(user)
        self.stdout.write(f'Создано арендаторов: {len(users)}')
        return users

    def _create_listings(self, landlords):
        anna, max_ = landlords
        listings_data = [
            (anna, 'Уютная квартира в центре Берлина', 'Светлая квартира с видом на парк, рядом метро', 'Berlin', 'Mitte', 'apartment', 2, 85),
            (anna, 'Просторный дом с садом', 'Двухэтажный дом для всей семьи, есть парковка', 'Munich', 'Schwabing', 'house', 4, 150),
            (anna, 'Компактная студия для одного', 'Идеально для командировки или коротких поездок', 'Hamburg', 'Altona', 'studio', 1, 55),
            (max_, 'Комната в общей квартире', 'Тихая комната, общая кухня и ванная', 'Frankfurt', 'Bornheim', 'room', 1, 35),
            (max_, 'Апартаменты у реки', 'Панорамные окна, современный ремонт', 'Cologne', 'Deutz', 'apartment', 3, 120),
            (max_, 'Дом в пригороде Штутгарта', 'Тихий район, до центра 20 минут', 'Stuttgart', 'Degerloch', 'house', 3, 110),
            (anna, 'Стильная студия в Дюссельдорфе', 'Недавно отремонтирована, есть балкон', 'Düsseldorf', 'Flingern', 'studio', 1, 60),
            (max_, 'Квартира с террасой', 'Большая терраса с видом на город', 'Rees', 'Zentrum', 'apartment', 2, 75),
        ]

        listings = []
        for owner, title, desc, city, district, ptype, rooms, price in listings_data:
            listing, created = Listing.objects.get_or_create(
                title=title,
                defaults={
                    'owner': owner,
                    'description': desc,
                    'city': city,
                    'district': district,
                    'property_type': ptype,
                    'rooms': rooms,
                    'price_per_night': price,
                    'views_count': 0,
                }
            )
            listings.append(listing)
        self.stdout.write(f'Создано объявлений: {len(listings)}')
        return listings

    def _create_bookings(self, tenants, listings):
        ivan, olga = tenants
        today = date.today()

        bookings_data = [
            # (tenant, listing, date_from, date_to, status)
            (ivan, listings[0], today - timedelta(days=20), today - timedelta(days=15), Booking.CONFIRMED),
            (olga, listings[1], today - timedelta(days=10), today - timedelta(days=5), Booking.CONFIRMED),
            (ivan, listings[2], today + timedelta(days=5), today + timedelta(days=10), Booking.PENDING),
            (olga, listings[3], today + timedelta(days=15), today + timedelta(days=20), Booking.CONFIRMED),
            (ivan, listings[4], today - timedelta(days=30), today - timedelta(days=25), Booking.CANCELLED),
        ]

        bookings = []
        for tenant, listing, date_from, date_to, status in bookings_data:
            days = (date_to - date_from).days
            total_price = days * listing.price_per_night
            booking, created = Booking.objects.get_or_create(
                tenant=tenant, listing=listing, date_from=date_from,
                defaults={'date_to': date_to, 'total_price': total_price, 'status': status}
            )
            bookings.append(booking)
        self.stdout.write(f'Создано бронирований: {len(bookings)}')
        return bookings

    def _create_reviews(self, bookings):
        # отзывы только для подтверждённых и уже завершившихся бронирований
        reviews_data = [
            (bookings[0], 5, 'Отличная квартира, всё понравилось!'),
            (bookings[1], 4, 'Хороший дом, но далеко от центра'),
        ]

        reviews = []
        for booking, rating, comment in reviews_data:
            review, created = Review.objects.get_or_create(
                booking=booking,
                defaults={'author': booking.tenant, 'rating': rating, 'comment': comment}
            )
            reviews.append(review)
        self.stdout.write(f'Создано отзывов: {len(reviews)}')
        return reviews