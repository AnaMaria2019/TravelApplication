from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

import string
import json
import random
import time
from datetime import datetime, date
from django.http import HttpResponse
from celery import shared_task, current_task
from celery_progress.backend import ProgressRecorder
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from .models import User, UserProfile, Search, Flight, Accommodation


def string_to_int(s):
    n = 0
    for c in s:
        if c.isdigit():
            n = n * 10 + int(c)

    return n


def string_to_float(s):
    new_string = ''
    for c in s:
        if c == ',':
            new_string += '.'
        else:
            new_string += c

    return float(new_string)


def get_data_from_flight(flight):
    flight_depart_time = flight.find('span', {"class": "depart-time"}).get_text()
    flight_depart_time = flight_depart_time.replace('\n', '')
    flight_arrival_time = flight.find('span', {"class": "arrival-time"}).get_text()
    flight_arrival_time = flight_arrival_time.replace('\n', '')
    flight_company = flight.find('div', {"class": "bottom"}).get_text()
    flight_company = flight_company.replace('\n', '')

    return flight_depart_time, flight_arrival_time, flight_company


@shared_task
def scrape_flight(url, username):
    opts = webdriver.FirefoxOptions()
    opts.headless = True
    driver = webdriver.Firefox(
        executable_path='D:\\1_Ana\\3_Info\\11_Facultate\\Anul_III\\Licenta\\CityClusters\\geckodriver', options=opts
    )
    driver.get(url)

    time.sleep(45)
    page = driver.page_source
    driver.close()
    soup = BeautifulSoup(page, 'html.parser')

    flight_grid = soup.find_all('div', {"class": "inner-grid keel-grid"})
    if flight_grid is None:
        return 'There is no flight!'

    ind = 0

    try:
        curr_flight = flight_grid[ind]
    except (IndexError, TypeError):
        return 'There is no flight!'
    else:
        best = curr_flight.find('div', {"class": "bfLabel bf-best"})

        while best is None:
            ind += 1
            try:
                curr_flight = flight_grid[ind]
            except (IndexError, TypeError):
                return 'There is no flight!'
            else:
                best = curr_flight.find('div', {"class": "bfLabel bf-best"})

    flight = curr_flight.find_all('div', {"class": "result-column"})[0]

    flight1 = flight.find_all('div', {"class": "section times"})[0]
    flight1_depart_time, flight1_arrival_time, flight1_company = get_data_from_flight(flight1)

    flight2 = flight.find_all('div', {"class": "section times"})[1]

    flight2_depart_time, flight2_arrival_time, flight2_company = get_data_from_flight(flight2)

    """
    price_div = curr_flight.find('div', {"class": "col-price result-column"})
    price = price_div.find('span', {"class": "price-text"}).get_text()
    int_price = string_to_int(price)
    link = price_div.find('a')
    full_link = "https://www.momondo.ro/" + link['href']
    """

    price_span = curr_flight.find('span', id=lambda x: x and x.endswith('-price-text'))
    price = price_span.get_text()
    int_price = string_to_int(price)
    print(int_price)
    provider_name = curr_flight.find('span', {'class': "providerName"}).get_text().replace('\n', '')
    # print('Price {} using the provider {}'.format(price, provider_name))
    link = curr_flight.find('a', id=lambda x: x and x.endswith('-booking-link'))
    href = link['href']
    full_link = "https://www.momondo.ro/" + href
    print(full_link)
    # print(book_flight_link)

    user = User.objects.get(username=username)
    print(username)
    current_userprofile = user.profile.first()
    last_search = Search.objects.filter(userprofile=current_userprofile).last()

    """ Extract from the budget the total price of the flight """
    nr_persons = last_search.nr_persons
    int_nr_persons = int(nr_persons)
    budget = last_search.remained_budget
    print("Initial budget: {}".format(budget))
    new_budget = budget - (int_price * int_nr_persons)

    if new_budget < 0:
        return 'Your budget is not enough!'

    """ Update the budget of the last search operated by the current user """
    last_search.remained_budget = new_budget

    """ Create flight object for the resulting solution """
    flight_result = Flight.objects.create(
        f1_depart_time=flight1_depart_time,
        f1_arrival_time=flight1_arrival_time,
        f2_depart_time=flight2_depart_time,
        f2_arrival_time=flight2_arrival_time,
        price=int_price * int_nr_persons,
        f1_provider=flight1_company,
        f2_provider=flight2_company,
        url_book_flights=full_link
    )
    print(flight_result)

    """ Associate the obtained flight with the last search operated by the current user """
    last_search.flight = flight_result
    last_search.save()

    return 'Your best solution for the flight is found!'


@shared_task
def scrape_booking(username):
    user = User.objects.get(username=username)
    current_userprofile = user.profile.first()
    last_search = Search.objects.filter(userprofile=current_userprofile).last()
    budget_ac = last_search.remained_budget

    # destination = 'Milano'
    destination = last_search.destination
    print(destination)
    start_date = last_search.start_date
    end_date = last_search.end_date
    start_date_str = start_date.strftime("%Y-%m-%d")  # Convert Date do String
    end_date_str = end_date.strftime("%Y-%m-%d")  # Convert Date to String
    nr_persons = last_search.nr_persons
    nr_rooms = last_search.nr_rooms

    start_date_year = datetime.strptime(start_date_str, '%Y-%m-%d').year
    start_date_month = datetime.strptime(start_date_str, '%Y-%m-%d').month
    start_date_day = datetime.strptime(start_date_str, '%Y-%m-%d').day
    # print(start_date_year, start_date_month, start_date_day)

    end_date_year = datetime.strptime(end_date_str, '%Y-%m-%d').year
    end_date_month = datetime.strptime(end_date_str, '%Y-%m-%d').month
    end_date_day = datetime.strptime(end_date_str, '%Y-%m-%d').day
    # print(end_date_year, end_date_month, end_date_day)

    today_year = date.today().year
    today_month = date.today().month
    today_day = date.today().day
    # print(today_year, today_month, today_day)

    url = 'https://www.booking.com/'

    opts = webdriver.FirefoxOptions()
    opts.headless = True
    driver = webdriver.Firefox(
        executable_path='D:\\1_Ana\\3_Info\\11_Facultate\\Anul_III\\Licenta\\CityClusters\\geckodriver', options=opts
    )
    driver.get(url)

    # Accept cookies.
    time.sleep(5)
    driver.find_element_by_xpath(
        "//button[contains(@data-gdpr-consent, 'accept') or contains(@id, 'onetrust-accept-btn-handler')]"
    ).click()

    # Find the input for entering the destination.
    destination_input = driver.find_element_by_id('ss')
    # Add the destination in the input.
    destination_input.send_keys(destination)

    # Find the input for entering the dates for check-in and check-out.
    driver.find_element_by_xpath("//div[contains(@class, 'xp__dates-inner')]").click()
    # driver.find_element_by_xpath("//div[contains(@data-bui-ref, 'calendar-content')]").click()

    if today_year == start_date_year:
        current_month = True
        for m in range(today_month, start_date_month):
            current_month = False

            button_1 = driver.find_element_by_xpath("//div[contains(@data-bui-ref, 'calendar-next')]")
            button_1.click()
            # time.sleep(1)

        if current_month and start_date_day >= today_day:
            driver.find_element_by_xpath("//td[contains(@data-date, '" + start_date_str + "')]").click()
        elif not current_month:
            driver.find_element_by_xpath("//td[contains(@data-date, '" + start_date_str + "')]").click()

        time.sleep(1)

        if end_date_month - start_date_month in [0, 1]:
            driver.find_element_by_xpath("//td[contains(@data-date, '" + end_date_str + "')]").click()
        else:
            for m in range(start_date_month, end_date_month):
                driver.find_element_by_xpath("//div[contains(@data-bui-ref, 'calendar-next')]").click()
                # time.sleep(1.5)
            driver.find_element_by_xpath("//td[contains(@data-date, '" + end_date_str + "')]").click()
    else:
        for m in range(12 - start_date_month + 1):
            driver.find_element_by_xpath("//div[contains(@data-bui-ref, 'calendar-next')]").click()
            # time.sleep(1.5)

        # Pe Booking se pot cauta cazari pana in anul urmator maxim septembrie.
        # De verificat daca utilizatorul a introdus
        # start_date si end_date ce se incadreaza in aceste conditii.

        for m in range(start_date_month):
            driver.find_element_by_xpath("//div[contains(@data-bui-ref, 'calendar-next')]").click()
            # time.sleep(1.5)
        driver.find_element_by_xpath("//td[contains(@data-date, '" + start_date + "')]").click()

        if end_date_month - start_date_month in [0, 1]:
            driver.find_element_by_xpath("//td[contains(@data-date, '" + end_date + "')]").click()
        else:
            for m in range(start_date_month, end_date_month):
                driver.find_element_by_xpath("//div[contains(@data-bui-ref, 'calendar-next')]").click()
                # time.sleep(1)
            driver.find_element_by_xpath("//td[contains(@data-date, '" + end_date + "')]").click()

    # Find the input for entering the number of persons and the number of rooms.
    driver.find_element_by_xpath("//label[contains(@id, 'xp__guests__toggle')]").click()

    if int(nr_persons) < 2:
        driver.find_element_by_xpath(
            "//div[contains(@class, 'sb-group__field-adults')] \
            //button[contains(@class, 'bui-stepper__subtract-button')]"
        ).click()
    elif int(nr_persons) > 2:
        for p in range(int(nr_persons) - 2):
            driver.find_element_by_xpath(
                "//div[contains(@class, 'sb-group__field-adults')]//button[contains(@class, 'bui-stepper__add-button')]"
            ).click()
            # time.sleep(1)

    if int(nr_rooms) > 1:
        for r in range(int(nr_rooms) - 1):
            driver.find_element_by_xpath(
                "//div[contains(@class, 'sb-group__field-rooms')]//button[contains(@class, 'bui-stepper__add-button')]"
            ).click()
            # time.sleep(1)

    # Click on the button to search for results.
    driver.find_element_by_class_name('sb-searchbox__button').click()

    # Wait until the list of hotels is loaded.
    wait = WebDriverWait(driver, timeout=7)
    try:
        wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'sr-hotel__title')))
    except TimeoutException:
        driver.close()
        return 'No accommodation was found!'
    else:
        try:
            driver.find_element_by_xpath(
                "//li[contains(@class, 'sort_category') and contains(@class, 'sort_review_score_and_price')]"
            ).click()
            time.sleep(1.2)
        except ElementNotInteractableException:
            driver.find_element_by_id('sortbar_dropdown_button').click()
            driver.find_element_by_xpath(
                "//li[contains(@class, 'sort_category') and contains(@class, 'sort_review_score_and_price')]"
            ).click()
            time.sleep(1.2)

        accommodations = []
        for i in range(2):
            while True:
                try:
                    wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'sr-hotel__title')))
                except StaleElementReferenceException:
                    print("The element is no longer attached to the DOM, continue with the next page!")
                    continue
                except TimeoutException:
                    break
                else:
                    time.sleep(1.2)
                    """
                    acc_names = driver.find_elements_by_class_name('sr-hotel__name')
                    for name in acc_names:
                        print(name.text)
                    """
                    accommodation_containers = driver.find_elements_by_class_name('sr_item_content')

                    for container in accommodation_containers:
                        accommodation = {}
                        attributes_found = 0

                        try:
                            acc_h3 = container.find_element_by_class_name('sr-hotel__title')
                        except NoSuchElementException:
                            continue
                        else:
                            attributes_found += 1
                            accommodation['url'] = acc_h3.find_element_by_class_name('hotel_name_link').get_attribute(
                                'href')

                        try:
                            acc_name = container.find_element_by_class_name('sr-hotel__name')
                        except NoSuchElementException:
                            continue
                        else:
                            attributes_found += 1
                            accommodation['name'] = acc_name.text

                        try:
                            acc_price = container.find_element_by_class_name('bui-price-display__value')
                        except NoSuchElementException:
                            continue
                        else:
                            attributes_found += 1
                            accommodation['price'] = string_to_int(acc_price.text)

                        try:
                            acc_score = container.find_element_by_class_name('bui-review-score__badge')
                        except NoSuchElementException:
                            accommodation['score'] = 2.5
                        else:
                            attributes_found += 1
                            accommodation['score'] = string_to_float(acc_score.text)

                        accommodations.append(accommodation)

                    time.sleep(1)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1500);")
                    try:
                        last_page = driver.find_element_by_xpath(
                            "//li[contains(@class, 'bui-pagination__next-arrow')]"
                        ).click()
                        # time.sleep(1.5)
                    except NoSuchElementException:
                        driver.find_element_by_xpath(
                            "//li[contains(@class, 'bui-pagination__item') \
                             and contains(@class, 'bui-pagination__item--disabled')]"
                        )
                        break
                    """else:
                        time.sleep(1.5)"""
                    break

        if len(accommodations) == 0:
            return 'No accommodation was found!'

        sorted_accommodations = sorted(accommodations, reverse=True, key=lambda it: (it['price'], it['score']))
        # print(len(sorted_accommodations))
        # print(sorted_accommodations)

        driver.close()

        found = False
        for ac in sorted_accommodations:
            if budget_ac - ac['price'] >= 0:
                found = True
                accommodation_obtained = Accommodation.objects.create(
                    name=ac['name'],
                    location=destination,
                    score=ac['score'],
                    price=ac['price'],
                    url_book_accommodation=ac['url']
                )
                print(accommodation_obtained)

                remained_budget = last_search.remained_budget - ac['price']
                last_search.remained_budget = remained_budget

                last_search.accommodation = accommodation_obtained
                last_search.save()
                break
        if not found:
            return 'Your budget is not enough!'

    return "Your perfect accommodation in {} was found!".format(destination)
