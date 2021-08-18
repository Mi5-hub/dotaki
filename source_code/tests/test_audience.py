import pandas as pd
import unittest, json
from django.contrib.auth.models import User
from django.http.response import HttpResponseNotAllowed
from django.test import Client
from django.urls import reverse

class TestAudience(unittest.TestCase):
    "Test for all endpoint related to the Audience page."

    def setUp(self):
        self.client = Client()
        s = self.client.session
        s.update({
            'client_id': '1684351428471021' # Jacadi's ID
        })
        s.save()
        User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary@1234')
        self.client.login(username='temporary', password='temporary@1234')
        return super().setUp()

    def tearDown(self):
        User.objects.filter(username='temporary').delete()
        return super().tearDown()

    def test_chart_none_post_request(self):
        response = self.client.post(reverse('get-audience-chart-data'), None)
        self.assertEqual(response.status_code, 400)

    def test_chart_empty_post_request(self):
        response = self.client.post(reverse('get-audience-chart-data'), {})
        self.assertEqual(response.status_code, 400)

    def test_chart_bad_method(self):
        response = self.client.get(reverse('get-audience-chart-data'))
        self.assertIsInstance(response, HttpResponseNotAllowed)
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(reverse('get-audience-chart-data'))
        self.assertIsInstance(response, HttpResponseNotAllowed)
        self.assertEqual(response.status_code, 405)

    def test_chart_bad_date(self):
        # False date_start
        params = {
            'date_start': 1999,
            'date_end': '1999-01-15',
            'device_type': 'Unfiltered',
            'page_type': 'Unfiltered',
            'group_segments': False,
            'compute_undefined': False
        }
        response = self.client.post(reverse('get-audience-chart-data'), params)
        self.assertEqual(response.status_code, 400)
        # False date_end
        params = {
            'date_start': '1999-01-01',
            'date_end': '%%%*^',
            'device_type': 'Unfiltered',
            'page_type': 'Unfiltered',
            'group_segments': False,
            'compute_undefined': False
        }
        response = self.client.post(reverse('get-audience-chart-data'), params)
        self.assertEqual(response.status_code, 400)
        # False date_start en date_end
        params = {
            'date_start': 'lalalala',
            'date_end': 'un deux trois',
            'device_type': 'Unfiltered',
            'page_type': 'Unfiltered',
            'group_segments': False,
            'compute_undefined': False
        }
        response = self.client.post(reverse('get-audience-chart-data'), params)
        self.assertEqual(response.status_code, 400)

    def test_chart_bad_device_type(self):
        params = {
            'date_start': '1999-01-01',
            'date_end': '1999-01-15',
            'device_type': 'not a device',
            'page_type': 'Unfiltered',
            'group_segments': False,
            'compute_undefined': False
        }
        response = self.client.post(reverse('get-audience-chart-data'), params)
        self.assertEqual(response.status_code, 400)

    def test_chart_success(self):
        #Test success query -> caching the result to minimise the bigquery queries
        params = {
            'date_start': '1999-01-01',
            'date_end': '1999-01-15',
            'device_type': 'Unfiltered',
            'page_type': 'Unfiltered',
            'group_segments': False,
            'compute_undefined': False
        }
        response = self.client.post(reverse('get-audience-chart-data'), params)
        print('response.content :')
        print(response.content)
        print('response.status_code :')
        print(response.status_code)
        print('response.context :')
        print(response.context)
        self.assertEqual(response.status_code, 200)

        #Test if page_type is not what is expected
        #Test if group_segments is not what is expected
        #Test if compute_undefined is not what is expected

    def test_chart_data_consistency(self):
        #TODO: Test for a specific setup, if the given dataframe is still the same over time
        params = {
            'date_start': '2021-05-01',
            'date_end': '2021-08-01',
            'device_type': 'Unfiltered',
            'page_type': 'Unfiltered',
            'group_segments': False,
            'compute_undefined': False
        }
        response = self.client.post(reverse('get-audience-chart-data'), params)
        new_df = pd.read_json(response.content.decode('utf-8'))
        old_df = pd.read_json('tests/chart_data_test.json')
        self.assertTrue(new_df.equals(old_df))

    # def test_save_data_to_json(self):
    #     """
    #     Used only to save data to json file
    #     """
    #     params = {
    #         'date_start': '2021-05-01',
    #         'date_end': '2021-08-01',
    #         'device_type': 'Unfiltered',
    #         'page_type': 'Unfiltered',
    #         'group_segments': False,
    #         'compute_undefined': False
    #     }
    #     response = self.client.post(reverse('get-audience-chart-data'), params)
    #     print(response.content)
    #     print(type(response.content.decode("utf-8")))
    #     with open('chart_data_test.json', 'w') as f:
    #         json.dump(json.loads(response.content.decode("utf-8")), f)

    def test_get_page_types_bad_method(self):
        # Test for two clients if the return is not blank
        response = self.client.post(reverse('get-page-types'), {})
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(reverse('get-page-types'), {})
        self.assertEqual(response.status_code, 405)

    def test_get_page_types_not_blank(self):
        # Check if actual client is not blank
        response = self.client.get(reverse('get-page-types'))
        self.assertNotEqual(json.loads(response.content.decode('utf-8'))['page_types'], {})

        # Check if fail attempt is blank
        s = self.client.session
        s.update({
            'client_id': '222'
        })
        s.save()
        response = self.client.get(reverse('get-page-types'))
        self.assertEqual(json.loads(response.content.decode('utf-8'))['page_types'], {})
