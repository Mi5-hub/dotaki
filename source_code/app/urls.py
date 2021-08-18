# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from app import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    # The audience page
    path('audience/', views.audience, name='audience'),
    path('get-audience-chart-data/', views.get_audience_chart_data, name='get-audience-chart-data'),
    path('get-page-types/', views.get_page_types, name='get-page-types'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
