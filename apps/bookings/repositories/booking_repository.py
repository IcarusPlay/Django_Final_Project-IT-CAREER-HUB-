from django.db.models import Q
from apps.bookings.models import Booking


class BookingRepository:

    @staticmethod
    def get_by_id(booking_id):
        # select_related('listing', 'tenant') - сразу подтягиваем и объявление, и арендатора
        # одним JOIN-запросом (та же оптимизация N+1, что и в ListingRepository)
        return Booking.objects.select_related('listing', 'tenant').filter(id=booking_id).first()

    @staticmethod
    def get_by_tenant(tenant):
        # Все бронирования конкретного арендатора - для страницы "Мои бронирования"
        return Booking.objects.filter(tenant=tenant).select_related('listing')

    @staticmethod
    def get_by_listing(listing):
        return Booking.objects.filter(listing=listing).select_related('tenant')

    @staticmethod
    def get_by_landlord(landlord):
        # listing__owner=landlord - двойное подчёркивание означает "перейти по связи":
        # мы фильтруем по полю owner МОДЕЛИ Listing, к которой прикреплена бронь через
        # ForeignKey listing. Так одним запросом находим все брони на ВСЕ объявления
        # этого арендодателя, не выбирая сначала список его объявлений отдельно.
        return Booking.objects.filter(listing__owner=landlord).select_related('listing', 'tenant')

    @staticmethod
    def count_pending_for_landlord(landlord):
        # Для бейджа "сколько заявок ожидает решения" в навбаре арендодателя
        return Booking.objects.filter(listing__owner=landlord, status=Booking.PENDING).count()

    @staticmethod
    def create(tenant, listing, date_from, date_to, total_price):
        return Booking.objects.create(
            tenant=tenant,
            listing=listing,
            date_from=date_from,
            date_to=date_to,
            total_price=total_price,
            status=Booking.PENDING,  # любое новое бронирование начинается со статуса "ожидает"
        )

    @staticmethod
    def set_status(booking, new_status):
        booking.status = new_status
        booking.save()
        return booking

    @staticmethod
    def set_tenant_notified(booking, notified):
        # update_fields=['tenant_notified'] - явно указываем что сохраняем ТОЛЬКО это поле,
        # а не весь объект целиком. Это чуть эффективнее (UPDATE запрос меньше), и главное -
        # безопаснее: если где-то параллельно менялись другие поля этого же объекта
        # в памяти (в другой части кода в рамках того же запроса), они случайно не перезапишутся
        booking.tenant_notified = notified
        booking.save(update_fields=['tenant_notified'])
        return booking

    @staticmethod
    def count_unseen_notifications(tenant):
        # Считаем заявки, статус которых изменился (confirmed/rejected), но арендатор
        # ещё не видел это изменение (tenant_notified всё ещё False)
        return Booking.objects.filter(
            tenant=tenant,
            tenant_notified=False,
            status__in=[Booking.CONFIRMED, Booking.REJECTED],
        ).count()

    @staticmethod
    def mark_all_notified(tenant):
        # Массовое обновление одним SQL-запросом (UPDATE ... WHERE ...) вместо цикла
        # "получить все объекты в Python, поменять поле у каждого, сохранить по одному" -
        # значительно быстрее при большом количестве записей
        Booking.objects.filter(tenant=tenant, tenant_notified=False).update(tenant_notified=True)

    @staticmethod
    def has_confirmed_booking(tenant, listing):
        return Booking.objects.filter(
            tenant=tenant,
            listing=listing,
            status=Booking.CONFIRMED,
        ).exists()

    @staticmethod
    def has_date_conflict(listing, date_from, date_to, exclude_booking_id=None, statuses=None):
        # Ключевая функция для защиты от двойного бронирования. Математика пересечения
        # двух отрезков времени: [start1, end1] и [start2, end2] пересекаются тогда
        # и только тогда, когда start1 < end2 И start2 < end1 (если хотя бы одно из этих
        # условий не выполняется - отрезки не пересекаются, один целиком до или после другого).
        # Здесь listing - это "новый" отрезок (date_from, date_to), с которым сравниваем
        # уже существующие брони этого объявления (тоже listing, но со своими датами).

        # По умолчанию проверяем конфликт против PENDING и CONFIRMED броней - именно эти
        # два статуса "занимают" даты. CANCELLED и REJECTED не считаются - эти даты снова свободны.
        if statuses is None:
            statuses = [Booking.PENDING, Booking.CONFIRMED]

        qs = Booking.objects.filter(
            listing=listing,
            status__in=statuses,
        ).filter(
            # date_from__lt=date_to - "дата начала существующей брони меньше даты окончания новой"
            # date_to__gt=date_from - "дата окончания существующей брони больше даты начала новой"
            # Вместе - именно то условие пересечения отрезков, описанное выше
            Q(date_from__lt=date_to) & Q(date_to__gt=date_from)
        )

        # exclude_booking_id используется когда мы проверяем саму эту же бронь на конфликт
        # с ДРУГИМИ (например при подтверждении - см. BookingService.confirm()) - иначе
        # бронь "конфликтовала" бы сама с собой, находя саму себя в списке
        if exclude_booking_id:
            qs = qs.exclude(id=exclude_booking_id)

        # .exists() эффективнее чем .count() > 0 - база данных может остановиться
        # на первой же найденной строке, не считая остальные
        return qs.exists()

    @staticmethod
    def get_active_date_ranges(listing):
        # Отдаёт занятые диапазоны дат для конкретного объявления - используется
        # публичным эндпоинтом /booked-ranges/, чтобы фронтенд мог проверить доступность
        # дат ДО отправки запроса на бронирование, а не только после ошибки от сервера.
        # .values('date_from', 'date_to') - вместо полных объектов Booking возвращаем
        # только словари с двумя нужными полями, этого достаточно для проверки на фронте.
        qs = Booking.objects.filter(
            listing=listing,
            status__in=[Booking.PENDING, Booking.CONFIRMED],
        ).values('date_from', 'date_to')
        return list(qs)
