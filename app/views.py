import json
import pandas as pd
import math

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, TemplateView
from django.core.exceptions import ObjectDoesNotExist

# It's a form for creating users, which comes with Django.
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse_lazy
from django.contrib import messages

from .models import City, User, UserProfile, Search
from .forms import SearchForm
from .tasks import scrape_flight, scrape_booking


import json
from django.http import HttpResponse
import random
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from celery.result import AsyncResult

# Create your views here.


def euclidean_distance(city_1, city_2):
    loss = 0
    for i in range(len(city_1)):
        loss += (city_1[i] - city_2[i]) ** 2

    loss = math.sqrt(loss)
    return loss


def welcome(request):
    return render(request, 'app/home_welcome.html')


def about(request):
    return render(request, 'app/about.html')


class SignUpView(CreateView):
    # 'CreateView' is a generic class view that uses a form to create, validate and save new model objects.
    form_class = UserCreationForm
    template_name = "app/signup_form.html"
    # success_url = reverse_lazy('app_welcome')
    model = User

    def form_valid(self, form):
        data = form.cleaned_data
        user = User.objects.create_user(username=data['username'],
                                        password=data['password1'])
        UserProfile.objects.create(user=user)
        return redirect('app_welcome')


class LoginView(TemplateView):
    template_name = 'login_form.html'

    def get_context_data(self):
        form = AuthenticationForm()
        return {'form': form}

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(username=data['username'],
                                password=data['password'])
            login(request, user)
            return redirect(reverse_lazy('app_welcome'))
        else:
            return render(request, "app/login_form.html", {"form": form})


def divide_list_in_groups(cities_l, n):
    for i in range(0, len(cities_l), n):
        yield cities_l[i:i+n]


@login_required
def choose_destinations(request):
    current_user = request.user
    current_userprofile = current_user.profile.first()

    if current_userprofile.has_selected_favorites is True:
        # Redirect the user to the page for completing the form.
        return redirect('app_search_form')

    # cities = City.objects.all()
    random_cities = []
    selected_pks = []

    ibiza = City.objects.get(city='ibiza')
    selected_pks.append(ibiza.pk)
    mamaia = City.objects.get(city='mamaia')
    selected_pks.append(mamaia.pk)
    venice = City.objects.get(city='venice')
    selected_pks.append(venice.pk)
    santorini = City.objects.get(city='santorini')
    selected_pks.append(santorini.pk)
    porto = City.objects.get(city='porto')
    selected_pks.append(porto.pk)

    random_cities.append(ibiza)
    random_cities.append(mamaia)
    random_cities.append(venice)
    random_cities.append(santorini)
    random_cities.append(porto)

    for i in range(15):
        pk = random.randint(1, 1320)

        while pk in selected_pks:
            pk = random.randint(1, 1320)

        selected_pks.append(pk)
        city = City.objects.get(id=pk)
        random_cities.append(city)

    n = 4
    groups_of_four = list(divide_list_in_groups(random_cities, n))

    return render(request, 'app/choose_fav_destinations.html', {'groups': groups_of_four})


def fav_cities(request):
    # Get current logged-in user.
    current_user = request.user
    # Get his profile.
    current_userprofile = current_user.profile.first()
    fav_destinations = request.POST.getlist('destinations[]')

    # Add every selected destination to his favorites list.
    for destination in fav_destinations:
        destination_obj = City.objects.get(city=destination)
        current_userprofile.favorite_cities.add(destination_obj)
        current_userprofile.has_selected_favorites = True
        current_userprofile.save()

    response_data = {'message': 'Merge!'}

    print(current_userprofile.favorite_cities.all())
    # return redirect(reverse_lazy("app_welcome"))
    return HttpResponse(json.dumps(response_data), content_type="appication/json")


def search_form(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        context = {'to_location': False, 'from_location': False}

        if form.is_valid():
            all_valid = 0

            from_location = form.cleaned_data['from_location']
            print(from_location)
            try:
                from_location = City.objects.get(city=from_location)
            except ObjectDoesNotExist:
                print("Locatia de plecare introdusa nu exista!")
            else:
                all_valid += 1
                context['from_location'] = True

            to_location = form.cleaned_data['to_location']
            print(to_location)

            try:
                to_location = City.objects.get(city=to_location)
            except ObjectDoesNotExist:
                print("Locatia destinatie introdusa nu exista!")
            else:
                all_valid += 1
                context['to_location'] = True

            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            budget = form.cleaned_data['budget']
            nr_persons = form.cleaned_data['nr_persons']
            nr_rooms = form.cleaned_data['nr_rooms']

            if context['to_location'] and context['from_location']:
                from_location_code = from_location.city_code
                to_location_code = to_location.city_code
                url = 'https://www.momondo.ro/flight-search/{}-{}/{}/{}?sort=bestflight_a'.format(from_location_code,
                                                                                                  to_location_code,
                                                                                                  start_date,
                                                                                                  end_date)
                current_user = request.user
                current_userprofile = current_user.profile.first()
                Search.objects.create(
                    userprofile=current_userprofile,
                    destination=to_location.city,
                    from_airport=from_location_code,
                    to_airport=to_location_code,
                    initial_budget=budget,
                    remained_budget=budget,
                    start_date=start_date,
                    end_date=end_date,
                    nr_persons=nr_persons,
                    nr_rooms=nr_rooms
                )

                # start_date_str = start_date.strftime("%Y-%m-%d")  # Convert Date do String
                # end_date_str = end_date.strftime("%Y-%m-%d")  # Convert Date to String

                username = current_user.username
                job = scrape_flight.delay(url, username)

                messages.success(request, 'We are processing your data. Wait a moment and refresh this page to see \
                                the result.')

                return HttpResponseRedirect(reverse_lazy('app_show_flight') + '?job=' + job.id)
            else:
                form = SearchForm()
                context['form'] = form
                return render(request, 'app/search_form.html', context)
    else:
        form = SearchForm()
        context = {'to_location': True, 'from_location': True, 'form': form}

    return render(request, 'app/search_form.html', context)


def poll_state(request):
    """ A view to report the progress to the user """
    # data = 'Fail'
    if request.is_ajax():
        if 'task_id' in request.POST.keys() and request.POST['task_id']:
            task_id = request.POST['task_id']
            task = AsyncResult(task_id)
            print("Task state is: {}".format(task.state))  # PENDING
            # None when it's pending and Your best solution for.. when it's success
            print("Task result is {}".format(task.result))
            # data = task.result or task.state
            data = {'message': task.state, 'return_string': task.result}
        else:
            # data = 'No task_id in the request'
            data = {'message': 'No task_id in the request'}
    else:
        # data = 'This is not an ajax request'
        data = {'message': 'This is not an ajax request'}

    json_data = json.dumps(data)
    return HttpResponse(json_data, content_type='application/json')


def show_flight(request):
    if 'job' in request.GET:
        job_id = request.GET['job']
        job = AsyncResult(job_id)
        data = job.result or job.state
        context = {
            'data': data,
            'task_id': job_id,
        }
        return render(request, "app/show_flight.html", context)

    return render(request, 'app/show_flight.html')


def get_flight(request):
    current_user = request.user
    current_userprofile = current_user.profile.first()
    last_search = Search.objects.filter(userprofile=current_userprofile).last()

    from_air = last_search.from_airport
    to_air = last_search.to_airport
    flight = last_search.flight
    f1_depart_time = flight.f1_depart_time
    f1_arrival_time = flight.f1_arrival_time
    f2_depart_time = flight.f2_depart_time
    f2_arrival_time = flight.f2_arrival_time
    full_price = flight.price
    f1_provider = flight.f1_provider
    f2_provider = flight.f2_provider
    url_book = flight.url_book_flights

    response_data = {
        'from_airport': from_air,
        'to_airport': to_air,
        'f1_depart_time': f1_depart_time,
        'f1_arrival_time': f1_arrival_time,
        'f2_depart_time': f2_depart_time,
        'f2_arrival_time': f2_arrival_time,
        'full_price': full_price,
        'f1_provider': f1_provider,
        'f2_provider': f2_provider,
        'url_book': url_book
    }

    # Use JS to show in the page the flight resulted from the search of the user.
    # We pass the values using JSON.
    json_data = json.dumps(response_data)
    return HttpResponse(json_data, content_type='application/json')


def search_accommodation(request):
    current_user = request.user
    username = current_user.username

    current_userprofile = current_user.profile.first()
    last_search = Search.objects.filter(userprofile=current_userprofile).last()
    # start_date = last_search.start_date
    # end_date = last_search.end_date

    """ Convert dates to strings (scraper needs serializable objects and date type is not serializable)"""
    """
    start_date_str = start_date.strftime("%Y-%m-%d")  # Convert Date do String
    end_date_str = end_date.strftime("%Y-%m-%d")  # Convert Date to String
    """

    job = scrape_booking.delay(username)

    return HttpResponseRedirect(reverse_lazy('app_show_accommodation') + '?job=' + job.id)


def show_accommodation(request):
    if 'job' in request.GET:
        job_id = request.GET['job']
        job = AsyncResult(job_id)
        data = job.result or job.state
        context = {
            'data': data,
            'task_id': job_id,
        }
        return render(request, "app/show_accommodation.html", context)

    return render(request, 'app/show_accommodation.html')


def get_accommodation(request):
    current_user = request.user
    current_userprofile = current_user.profile.first()
    last_search = Search.objects.filter(userprofile=current_userprofile).last()
    destination = last_search.destination
    # print(destination)

    time.sleep(1)

    accommodation = last_search.accommodation
    name = accommodation.name
    location = accommodation.location
    score = accommodation.score
    price = accommodation.price
    url_book = accommodation.url_book_accommodation

    from_air = last_search.from_airport
    to_air = last_search.to_airport
    flight = last_search.flight
    f1_depart_time = flight.f1_depart_time
    f1_arrival_time = flight.f1_arrival_time
    f2_depart_time = flight.f2_depart_time
    f2_arrival_time = flight.f2_arrival_time
    full_price = flight.price
    f1_provider = flight.f1_provider
    f2_provider = flight.f2_provider
    url_book_flights = flight.url_book_flights

    """ Get recommendations """
    try:
        destination = City.objects.get(city=destination)
    except ObjectDoesNotExist:
        print("City does not exist!")
    else:
        id_cl = destination.id_cluster

        chosen_cities = list(current_userprofile.favorite_cities.all().values())
        current_cluster = list(City.objects.filter(id_cluster=id_cl).values())
        # print(current_cluster)  # It works! These are all the cities in the same cluster with the searched city.
        # print(chosen_cities)  # It works!

        with open('scaled_data.json') as js:
            loaded_json = json.load(js)
            df = pd.DataFrame(columns=['cost_scaled', 'temperature_scaled', 'humidity_scaled'])
            city_ind = {}
            i = 0

            for line in loaded_json:
                pandas_line = [line['cost_scaled'], line['temperature_scaled'], line['humidity_scaled']]
                city_ind[line['city']] = i
                df.loc[i] = pandas_line
                i += 1

            x = df.values
            score_list = []
            destination_ind = city_ind[destination.city]
            destination_cost = x[destination_ind][0]

            for neigh in current_cluster:
                if neigh['city'] == destination.city:  # Check if the city from the cluster is the current city
                    continue

                score = 0

                neigh_ind = city_ind[neigh['city']]
                neigh_ch = [
                    x[neigh_ind][0],
                    x[neigh_ind][1],
                    x[neigh_ind][2]
                ]
                print("Neighbour city {} has this ch: {}".format(neigh['city'], neigh_ch))
                neigh_cost = neigh_ch[0]

                for favourite_city in chosen_cities:
                    fav_ind = city_ind[favourite_city['city']]

                    fav_ch = [
                        x[fav_ind][0],
                        x[fav_ind][1],
                        x[fav_ind][2]
                    ]
                    print("Chosen city {} has this ch: {}".format(favourite_city['city'], fav_ch))
                    euclidean_score = euclidean_distance(neigh_ch, fav_ch)
                    score += euclidean_score

                # incercam sa minimizam diferenta dintre costul orasului explorat
                # si cel al orasului recomandat pentru a gasi oferte cat mai apropiate
                score += 1.3 * (neigh_cost - destination_cost)

                print("Score for {} is : {}".format(neigh, score))
                print()
                score_list.append((neigh, score))

            score_list = sorted(score_list, key=lambda y: y[1])
            # print()
            print("Top 3 recommendations are:", score_list[:3])

            dict_1, _ = score_list[0]
            dict_2, _ = score_list[1]
            dict_3, _ = score_list[3]

    time.sleep(1)
    # print(dict_1['city'], dict_2['city'], dict_3['city'])

    response_data = {
        'name': name,
        'location': location,
        'score': score,
        'price': price,
        'url_book': url_book,
        'from_airport': from_air,
        'to_airport': to_air,
        'f1_depart_time': f1_depart_time,
        'f1_arrival_time': f1_arrival_time,
        'f2_depart_time': f2_depart_time,
        'f2_arrival_time': f2_arrival_time,
        'full_price': full_price,
        'f1_provider': f1_provider,
        'f2_provider': f2_provider,
        'url_book_flights': url_book_flights,
        'recommendation_1': dict_1['city'],
        'recommendation_1_image': dict_1['image'],
        'recommendation_2': dict_2['city'],
        'recommendation_2_image': dict_2['image'],
        'recommendation_3': dict_3['city'],
        'recommendation_3_image': dict_3['image'],
    }

    # print(response_data['accommodation-1'], response_data['accommodation-2'], response_data['accommodation-3'])

    # Use JS to show in the page the accommodation resulted from the search of the user.
    # We pass the values using JSON.
    json_data = json.dumps(response_data)
    return HttpResponse(json_data, content_type='application/json')
