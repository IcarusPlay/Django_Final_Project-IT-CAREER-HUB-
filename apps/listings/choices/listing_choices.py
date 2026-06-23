from django.db import models


class PropertyType(models.TextChoices):
    APARTMENT = 'apartment', 'Apartment'
    HOUSE = 'house', 'House'
    ROOM = 'room', 'Room'
    STUDIO = 'studio', 'Studio'


class ListingStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
