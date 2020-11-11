from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
User = get_user_model()


class City(models.Model):
    city = models.CharField(max_length=100)
    image = models.ImageField(blank=True, null=True)
    cost = models.IntegerField()
    temperature = models.IntegerField()
    humidity = models.IntegerField()
    id_cluster = models.IntegerField()
    city_code = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return f"Destination {self.city} is located in cluster nr. {self.id_cluster}"


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile')
    has_selected_favorites = models.BooleanField(default=False)
    favorite_cities = models.ManyToManyField(City, related_name='user_favorites', blank=True)
    # search = models.ForeignKey(Search, on_delete=models.CASCADE, related_name='search')
    # searches = models.ManyToManyField(Search, related_name='user_searches', blank=True)

    def __str__(self):
        return f"Userprofile with id {self.pk} has username {self.user.username}"


class Flight(models.Model):
    f1_depart_time = models.CharField(max_length=150)
    f1_arrival_time = models.CharField(max_length=150)
    f2_depart_time = models.CharField(max_length=150)
    f2_arrival_time = models.CharField(max_length=150)
    price = models.PositiveIntegerField(blank=True, default=0)
    f1_provider = models.CharField(max_length=100, blank=True)
    f2_provider = models.CharField(max_length=100, blank=True)
    url_book_flights = models.CharField(max_length=600)

    def __str__(self):
        return f"Flight 1: {self.f1_depart_time} - {self.f1_arrival_time} from {self.f1_provider}, " \
               f"Flight 2: {self.f2_depart_time} - {self.f2_arrival_time} from {self.f2_provider} " \
               f"full price for all persons: {self.price}"


class Accommodation(models.Model):
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    score = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    url_book_accommodation = models.CharField(max_length=600)

    def __str__(self):
        return f"Accommodation name: {self.name} located in {self.location} has price {self.price}"


class Search(models.Model):
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='userprofile')
    flight = models.OneToOneField(Flight, on_delete=models.CASCADE, blank=True, null=True)
    accommodation = models.OneToOneField(Accommodation, on_delete=models.CASCADE, blank=True, null=True)
    destination = models.CharField(max_length=150)
    from_airport = models.CharField(max_length=150, null=True)
    to_airport = models.CharField(max_length=150, null=True)
    initial_budget = models.PositiveIntegerField()
    remained_budget = models.PositiveIntegerField()
    start_date = models.DateField(max_length=100)
    end_date = models.DateField(max_length=100)
    nr_persons = models.PositiveIntegerField(default=1)
    nr_rooms = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Search {self.pk}:  {self.from_airport} - {self.to_airport}, {self.start_date} - {self.end_date}, " \
               f"nr. rooms: {self.nr_rooms} and nr. persons: {self.nr_persons}"
