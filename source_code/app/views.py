# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import time, re
import pandas as pd
import pandas_gbq
from django.db import connection
from django.http.response import JsonResponse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from django import template

emotionals = ['Audacious', 'Emotives', 'Hedonists', 'Altruists', 'Homebodies']
rationals = ['Analyticals', 'Trend Setters', 'Straightforwards', 'Conventionals', 'Attentives']

@login_required(login_url="/login/")
def index(request):
    
    context = {}
    context['segment'] = 'index'

    html_template = loader.get_template( 'index.html' )
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def audience(request):
    context = {}
    context['segment'] = 'audience'

    html_template = loader.get_template( 'audience.html' )
    return HttpResponse(html_template.render(context, request))

@require_http_methods(["POST"])
@login_required(login_url="/login/")
def get_audience_chart_data(request):
    """
    This endpoint expects several parameters :
    `date_start` and `date_end`, formated YYYY-MM-DD, define the time slot on which the data must be queried. If one of this two params are changed, the cache is invalidated
    and the bigquery query will be re-executed anyway.
    `device_type` is either 'Unfiltered' (take both Desktop and Mobile), 'Desktop' (only Desktop) and 2 (only Mobile).
    `page_type` can be 'Unfiltered' (all pages will be computed), or any page returned by the related endpoint.
    `compute_undefined` is used to display 'Undefinied' values. It is not yet well tested.
    `group_segments` defines if all 10 segments should be displayed, or if they should be grouped as rationals and emotionals.
    The endpoint also needs the client_id, which is stored in the session when the user logs in.
    When queried, the endpoint will start by checking if the dates are the same since the last query and if it can find the data in cache. If not, it will query bigQuery
    for the relevent data, and cache it. It will then, regarding the parameters provided, compute the data and return it as a json object with three entries :
    chartdata : all the numeric values displayed in the chart.
    percentage : the percentage of each persona.
    personaslist : the list of personas.
    """
    start = time.time()

    if request.POST.get('date_start', False) is False or request.POST.get('date_end', False) is False or \
    request.POST.get('device_type', False) is False or request.POST.get('page_type', False) is False or \
    request.POST.get('group_segments', False) is False:
        return JsonResponse({'success': False, 'content': 'missing on required parameter, see documentation'}, status=400)

    if not re.match("^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$", str(request.POST['date_start'])) or \
    not re.match("^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$", str(request.POST['date_end'])):
        return JsonResponse({'success': False, 'content': 'date_start or date_end is not valid YYYY-MM-DD string'}, status=400)

    if request.POST.get('device_type', None) not in ['Unfiltered', 'Desktop', 'Mobile']:
        return JsonResponse({'success': False, 'content': 'device_type not on of : Unfiltered, Mobile or Desktop'}, status=400)


    response = {}
    print('Request params in get_audience_chart_data:')
    print(request.POST)

    cached_result = cache.get('whole_audience_dataframe')
    print('>>>>> Cached result : <<<<<')
    print(cached_result)

    query = f"""SELECT DATE(server_time) AS activity_date, user_id_zws, segment, device_type, page_type_referer, page_type, COUNT(segment) AS value
        FROM `dev-inscriber-251115.{request.session['client_id']}.user_activities_{request.session['client_id']}`
        WHERE DATE(server_time) > "{request.POST['date_start']}" AND DATE(server_time) < "{request.POST['date_end']}"
        GROUP BY segment, activity_date, user_id_zws, segment, device_type, page_type_referer, page_type
        ORDER BY activity_date"""

    print(query)

    if cached_result is None or query != cache.get('audience_query'): # No data found in cache, execute the bigquery request
        print(">>>>> No Data found in cache or query changed, requesting bigquery <<<<<")
        cache.set('audience_query', query)
        result_df = pandas_gbq.read_gbq(query, project_id='dev-inscriber-251115', use_bqstorage_api=True)  # Make an API request.
        result_df = result_df[result_df['segment'] != 'Undefined']
        print(">>>>> Query result: <<<<<")
        print(result_df)

        if result_df is not None:
            print('>>>>> caching results <<<<<')
            cache.set('whole_audience_dataframe', result_df)
            cached_result = result_df

    if request.POST.get('compute_undefined', 'false').lower() != 'true':
        cached_result = cached_result[cached_result['segment'].isin(emotionals + rationals)]

    if request.POST['device_type'] != 'Unfiltered':
        if request.POST['page_type'] != 'Unfiltered':
            response['chartdata'] = cached_result[(cached_result.page_type == request.POST['page_type']) & (cached_result.device_type == request.POST['device_type'])]["segment"].value_counts()
            response['percentage'] = cached_result[(cached_result.page_type == request.POST['page_type']) & (cached_result.device_type == request.POST['device_type'])]["segment"].value_counts(normalize=True) * 100
        else:
            response['chartdata'] = cached_result[cached_result.device_type == request.POST['device_type']]["segment"].value_counts()
            response['percentage'] = cached_result[cached_result.device_type == request.POST['device_type']]["segment"].value_counts(normalize=True) * 100
    elif request.POST['page_type'] != 'Unfiltered':
        response['chartdata'] = cached_result[cached_result.page_type == request.POST['page_type']]["segment"].value_counts()
        response['percentage'] = cached_result[cached_result.page_type == request.POST['page_type']]["segment"].value_counts(normalize=True) * 100
    else:
        response['chartdata'] = cached_result["segment"].value_counts()
        response['percentage'] = cached_result["segment"].value_counts(normalize=True) * 100

        # response['chartdata'] = response['chartdata'][response['chartdata'].index.isin(emotionals + rationals)]
        # response['percentage'] = response['percentage'][response['percentage'].index.isin(emotionals + rationals)]

    # group_segments handling
    if request.POST['group_segments'].lower() == 'true':
        grouped_result = pd.Series([0, 0], ['Emotionals', 'Rationals'])
        for index, value in response['chartdata'].items():
            if index in emotionals:
                grouped_result['Emotionals'] += value
            elif index in rationals:
                grouped_result['Rationals'] += value
        response['chartdata'] = grouped_result
    
    response['personaslist'] = response['chartdata'].index.tolist()
    ###

    print(">>>>> Final Result <<<<<")
    print(response['chartdata'])
    print(">>>>> Response Object <<<<<")
    # response object filling
    response['chartdata'] = response['chartdata'].tolist()
    response['percentage'] = response['percentage'].tolist()
    response['success'] = True
    print(response)
    ###
    print(f"Query took {time.time() - start} seconds")
    return JsonResponse(response)

@require_http_methods(["GET"])
@login_required(login_url="/login/")
def get_page_types(request):
    """
    The endpoint uses the client_id refered in the session to return a json object containing the related page types.
    """
    query = f"SELECT kpi_id, kpi_name FROM `kpis` WHERE client_id=\"{request.session['client_id']}\""
    page_types = {}
    with connection.cursor() as cursor:
        cursor.execute("use dotaki;")
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.execute("use web_app;")
        page_types = {idx: item[1] for idx, item in enumerate(result)}
    print(page_types)
    return JsonResponse(page_types)

@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template
        
        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:
    
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))
