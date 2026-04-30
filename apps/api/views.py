import time
import json
import datetime
import re
import urllib
import csv
import os
import subprocess
import math
import requests

# import pandas as pd
from django.core import serializers

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings as conf_settings
from requests.sessions import default_headers
from urllib.parse import quote

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


from apps.data.models import (
    Dataset,
    DATA_MAPPING,
    DatasetOrganization,
    Taxon,
)
from apps.data.helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
    SpeciesSearch,
    filter_occurrence,
)

from utils.decorators import json_ret
from utils.general import get_cache_or_set
from utils.solr_query import (
    SolrQuery,
    get_init_menu,
)
from utils.map_data import (
    convert_grid_to_coor,
    get_geojson,
    convert_x_coor_to_grid,
    convert_y_coor_to_grid,
)


from .cached import COUNTRY_ROWS, YEAR_ROWS

from conf.settings import ENV

OCCURRENCE_ROOT_TREE = [
    {"id": "t0000005", "data": {"name": "細菌界 Bacteria", "count": None}},
    {"id": "t0000007", "data": {"name": "原藻界 Chromista", "count": None}},
    {"id": "t0000004", "data": {"name": "古菌界 Archaea", "count": None}},
    {"id": "t0000008", "data": {"name": "真菌界 Fungi", "count": None}},
    {"id": "t0000009", "data": {"name": "動物界 Animalia", "count": None}},
    {"id": "t0000003", "data": {"name": "植物界 Plantae", "count": None}},
    {"id": "t0000006", "data": {"name": "原生生物界 Protozoa", "count": None}},
]


def _get_initial_occurrence_response():
    cached_response = cache.get("init_solr_resp")
    if cached_response:
        return cached_response

    solr = SolrQuery("taibif_occurrence")
    req = solr.request()
    resp = solr.get_response()
    if not resp:
        return None

    resp["menus"] = solr.get_menus()
    resp["elapsed"] = req["solr_response"]["responseHeader"]["QTime"] / 1000
    resp["tree"] = OCCURRENCE_ROOT_TREE
    cache.set("init_solr_resp", resp, 2592000)
    return resp

COORDINATE_SYSTEM_MAP = {
    "1": "EPSG:4326",  # WGS84 經緯度
    "2": "EPSG:3821",  # TWD67 經緯度
    "3": "EPSG:3824",  # TWD97 經緯度
    "4": "EPSG:3825",  # TWD97 / TM2 中央經線119度
    "5": "EPSG:3826",  # TWD97 / TM2 中央經線121度
    "6": "EPSG:3827",  # TWD67 / TM2 中央經線119度
    "7": "EPSG:3828",  # TWD67 / TM2 中央經線121度
    "8": (
        "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 "
        "+x_0=250000 +y_0=0 +ellps=GRS67 "
        "+towgs84=-752,-358,-179,-0.0000011698,0.0000018398,0.0000009822,0.00002329 "
        "+units=m +no_defs +type=crs"
    ),
    # TWD67 / TM2 中央經線121度修正版，根據中央研究院人社中心GIS專題中心說明修正
    "9": "EPSG:4236",  # 虎子山經緯度
}


def _get_epsg(code):
    return COORDINATE_SYSTEM_MAP.get((code or "1").strip())


def _format_coordinate_value(value):
    if value is None or not math.isfinite(value):
        return "NaN"
    return f"{value:.6f}"


def _get_transformer(source_system, destination_system):
    source_epsg = _get_epsg(source_system)
    if source_epsg is None:
        return None, "invalid source"

    destination_epsg = _get_epsg(destination_system)
    if destination_epsg is None:
        return None, "invalid destination"

    try:
        from pyproj import Transformer
    except ImportError:
        return None, "pyproj not installed"

    transformer = Transformer.from_crs(source_epsg, destination_epsg, always_xy=True)
    return (transformer, source_epsg, destination_epsg), None


def coordinate_convert(request):
    source_system = request.GET.get("source", request.GET.get("sourceSystem", "1"))
    destination_system = request.GET.get(
        "destination", request.GET.get("targetSystem", request.GET.get("tgt", "1"))
    )

    x = request.GET.get("x")
    y = request.GET.get("y")
    if x is None or y is None:
        return JsonResponse(
            {"error": "missing coord", "message": "x and y are required"},
            status=400,
        )

    try:
        x = float(x)
        y = float(y)
    except ValueError:
        return JsonResponse(
            {"error": "invalid coord", "message": "x and y must be numeric"},
            status=400,
        )

    transformer_result, err = _get_transformer(source_system, destination_system)
    if transformer_result is None:
        if err == "pyproj not installed":
            return JsonResponse({"error": err}, status=500)
        return JsonResponse({"error": err}, status=400)
    transformer, source_epsg, destination_epsg = transformer_result

    converted_x, converted_y = transformer.transform(x, y)
    return JsonResponse(
        {
            "src": {"x": x, "y": y, "datum": source_epsg},
            "dest": {
                "x": converted_x,
                "y": converted_y,
                "datum": destination_epsg,
            },
        }
    )


def coordinate_convert_batch(request):
    source_system = request.GET.get("source", request.GET.get("sourceSystem", "1"))
    destination_system = request.GET.get(
        "destination", request.GET.get("targetSystem", request.GET.get("tgt", "1"))
    )
    source_xy = request.GET.get("sourceXY")

    if request.method == "POST":
        source_xy = request.POST.get("sourceXY", source_xy)

    source_xy = (source_xy or "").strip()
    if not source_xy:
        return coordinate_convert(request)

    transformer_result, err = _get_transformer(source_system, destination_system)
    if transformer_result is None:
        if err == "pyproj not installed":
            return JsonResponse({"error": err}, status=500)
        return JsonResponse({"error": err}, status=400)
    transformer, source_epsg, destination_epsg = transformer_result

    lines = source_xy.split("\n")
    converted = []

    for line in lines:
        raw = line.strip()
        if not raw:
            converted.append("NaN,NaN")
            continue

        tokens = [p for p in re.split(r"[\s,]+", raw) if p != ""]
        if len(tokens) < 2:
            converted.append("NaN,NaN")
            continue

        source_x, source_y = tokens[0], tokens[-1]
        try:
            source_x = float(source_x)
            source_y = float(source_y)
        except ValueError:
            converted.append("NaN,NaN")
            continue

        dest_x, dest_y = transformer.transform(source_x, source_y)
        converted.append(
            f"{_format_coordinate_value(dest_x)},{_format_coordinate_value(dest_y)}"
        )

    return HttpResponse("\n".join(converted), content_type="text/plain; charset=utf-8")


def search_occurrence_v1_charts(request):
    year_start = 1000
    year_end = 2021
    lat_query, lng_query = "", ""

    solr_q_fq_list = []
    solr_fq = ""
    solr_q_list = []
    solr_q = "*:*"
    # print (list(request.GET.lists()))
    for term, values in list(request.GET.lists()):
        if term != "q":
            if term != "menu":
                if term == "year":
                    val = values[0].replace(",", " TO ")
                    solr_q_fq_list.append("{}:[{}]".format(term, val))
                    year_start = values[0].split(",", 1)
                    year_end = values[0].split(",", 2)
                elif term == "dataset":
                    solr_q_fq_list.append(
                        '{}:"{}"'.format("taibif_dataset_name", '" OR "'.join(values))
                    )
                elif term == "month":
                    solr_q_fq_list.append("{}:{}".format(term, " OR ".join(values)))
                elif term == "country":
                    solr_q_fq_list.append("{}:{}".format(term, " OR ".join(values)))
                elif term == "publisher":
                    solr_q_fq_list.append("{}:{}".format(term, " OR ".join(values)))
                # -----map------#
                elif term == "lat":
                    coor_list = [float(c) for c in values]
                    y1 = convert_y_coor_to_grid(min(coor_list))
                    y2 = convert_y_coor_to_grid(max(coor_list))
                    lat_query = (
                        "&fq={!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
                    )
                elif term == "lng":
                    coor_list = [float(c) for c in values]
                    x1 = convert_x_coor_to_grid(min(coor_list))
                    x2 = convert_x_coor_to_grid(max(coor_list))
                    lng_query = (
                        "&fq={!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"
                    )

        else:
            solr_q_list.append("{}:{}".format("_text_", " OR ".join(values)))

    if len(solr_q_list) > 0:
        solr_q = " AND ".join(solr_q_list)

    if len(solr_q_fq_list) > 0:
        solr_fq = " AND ".join(solr_q_fq_list)

    charts_year = []
    charts_month = []
    charts_dataset = []

    search_count = 0
    search_offset = 0
    search_results = []

    facet_dataset = (
        "dataset:{type:terms,field:taibif_dataset_name_zh,limit:-1,mincount:0}"
    )
    facet_month = "month:{type:range,field:month,start:1,end:13,gap:1}"
    facet_year = "year:{type:terms,field:year,limit:-1,mincount:0}"
    facet_json = (
        "json.facet={" + facet_dataset + "," + facet_month + "," + facet_year + "}"
    )

    url = f"http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=AND&q={solr_q}&fq={solr_fq}&{facet_json}{lng_query}{lat_query}"
    r = requests.get(url)

    if r.status_code == 200:
        data = r.json()
        search_count = data["response"]["numFound"]
        if search_count != 0:
            search_offset = data["response"]["start"]
            search_results = data["response"]["docs"]
            charts_year = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["year"]["buckets"]
            ]
            charts_month = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["month"]["buckets"]
            ]
            charts_dataset = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["dataset"]["buckets"]
            ]
        else:
            charts_year = [{"key": 0, "label": 0, "count": 0}]
            charts_month = [{"key": 0, "label": 0, "count": 0}]
            charts_dataset = [{"key": 0, "label": 0, "count": 0}]

    ret = {
        "charts": [
            {
                "key": "year",
                "label": "年份",
                "rows": charts_year,
            },
            {
                "key": "month",
                "label": "月份",
                "rows": charts_month,
            },
            {
                "key": "dataset",
                "label": "資料集",
                "rows": charts_dataset,
            },
        ],
    }
    return JsonResponse(ret)


def get_map_species(request):
    query_list = []
    for key, values in request.GET.lists():
        if key != "facet":
            query_list.append((key, values))
    solr = SolrQuery("taibif_occurrence")
    solr_url = solr.generate_solr_url(request.GET.lists())
    map_url = solr_url.replace("rows=20", "rows=10")
    r = requests.get(map_url)
    resp = {"count": 0}
    if r.status_code == 200:
        data = r.json()
        resp.update({"count": data["response"]["numFound"]})
        resp["results"] = data["response"]["docs"]

    return JsonResponse(resp)


def dataset_api_v3(request):

    params = request.GET

    # params 送進 DatasetSearch 之前先檢查
    validation_response = validate_params(params)
    if validation_response:
        return validation_response

    ds_search = DatasetSearch(list(params.lists()))
    result_d = ds_search.query.values()

    rows = [
        {
            "datasetName": x["title"] if "title" in x else None,
            "taibifDatasetID": (
                x["taibif_dataset_id"] if "taibif_dataset_id" in x else None
            ),
            "publisherID": x["organization_uuid"] if "organization_uuid" in x else None,
            "publisherName": (
                x["organization_name"] if "organization_name" in x else None
            ),
            "author": x["author"] if "author" in x else None,
            "datasetShortName": x["name"] if "name" in x else None,
            "publicationDate": (
                x["pub_date"].strftime("%Y-%m-%d")
                if "pub_date" in x and x["pub_date"] != None
                else None
            ),
            "datasetModifiedDate": (
                x["mod_date"].strftime("%Y-%m-%d")
                if "mod_date" in x and x["mod_date"] != None
                else None
            ),
            "gbifDatasetID": x["guid"] if "guid" in x else None,
            "core": x["dwc_core_type"].upper() if "dwc_core_type" in x else None,
            "license": x["data_license"] if "data_license" in x else "unknown",
            "doi": x["gbif_doi"] if "gbif_doi" in x else "test",
            "numberRecord": x["num_record"] if "num_record" in x else None,
            "numberOccurrence": x["num_occurrence"] if "num_occurrence" in x else None,
            "source": x["source"] if "source" in x else None,
        }
        for x in result_d
    ]

    api_response = JsonResponse(
        {
            "status": {"code": 200, "message": "Success"},
            "params": params,
            "count": len(rows),
            "data": rows,
        }
    )

    return api_response


def dataset_api(request):

    ds_search = DatasetSearch(list(request.GET.lists()))
    result_d = ds_search.query.values()

    rows = [
        {
            "datasetName": x["title"] if "title" in x else None,
            "taibifDatasetID": (
                str(x["taibif_dataset_id"]) if "taibif_dataset_id" in x else None
            ),
            "publisherID": (
                x["organization_uuid"]
                if "organization_uuid" in x and x["organization_uuid"] != None
                else None
            ),
            "publisherName": (
                x["organization_name"]
                if "organization_name" in x and x["organization_name"] != None
                else None
            ),
            "author": x["author"] if "author" in x and x["mod_date"] != None else None,
            "datasetShortName": x["name"],
            "publicationDate": (
                x["pub_date"].strftime("%Y-%m-%d")
                if "pub_date" in x and x["pub_date"] != None
                else None
            ),
            "datasetModifiedDate": (
                x["mod_date"].strftime("%Y-%m-%d")
                if "mod_date" in x and x["mod_date"] != None
                else None
            ),
            "gbifDatasetID": x["guid"] if "guid" in x and x["guid"] != None else None,
            "core": x["dwc_core_type"] if "dwc_core_type" in x else None,
            "license": (
                x["data_license"]
                if "data_license" in x and x["data_license"] != None
                else "unknown"
            ),
            "doi": (
                x["gbif_doi"] if "gbif_doi" in x and x["gbif_doi"] != None else "test"
            ),
            "numberRecord": (
                x["num_record"]
                if "num_record" in x and x["num_record"] != None
                else None
            ),
            "numberOccurrence": (
                x["num_occurrence"]
                if "num_occurrence" in x and x["num_occurrence"] != None
                else None
            ),
            "source": x["source"] if "source" in x else None,
            # 'citation' : x['citation'] if 'citation' in x else None,
            # 'resource' : x['resource'] if 'resource' in x else None,
        }
        for x in result_d
    ]

    return HttpResponse(json.dumps(rows), content_type="application/json")


def publisher_api_v3(request):

    params = request.GET

    # params 送進 PublisherSearch 之前先檢查
    validation_response = validate_params(params)
    if validation_response:
        return validation_response

    ds_search = PublisherSearch(list(params.lists()))
    result_d = ds_search.query.values()

    rows = [
        {
            "publisherID": (
                x["organization_gbif_uuid"] if "organization_gbif_uuid" in x else None
            ),
            "publisherName": x["name"] if "name" in x else None,
            "description": x["description"] if "description" in x else None,
            "administrativeContact": (
                x["administrative_contact"] if "administrative_contact" in x else None
            ),
            "technicalContact": (
                x["technical_contact"] if "technical_contact" in x else None
            ),
            "countryCode": x["country_code"] if "country_code" in x else None,
            "countryOrArea": x["country_or_area"] if "country_or_area" in x else None,
            "installations": x["installations"] if "installations" in x else None,
        }
        for x in result_d
    ]

    api_response = JsonResponse(
        {
            "status": {"code": 200, "message": "Success"},
            "params": params,
            "count": len(rows),
            "data": rows,
        }
    )

    return api_response


def publisher_api(request):
    dataset = []

    ds_search = PublisherSearch(list(request.GET.lists()))
    result_d = ds_search.query.values()

    rows = [
        {
            "publisherID": (
                x["organization_gbif_uuid"] if "organization_gbif_uuid" in x else None
            ),
            # 'id' : x['id'] if 'id' in x else None,
            "publisherName": x["name"],
            "countryCode": x["country_code"] if "country_code" in x else None,
            "description": x["description"] if "description" in x else None,
            "administrativeContact": (
                x["administrative_contact"] if "administrative_contact" in x else None
            ),
            "countryOrArea": x["country_or_area"] if "country_or_area" in x else None,
            "installations": x["installations"] if "installations" in x else None,
            "technicalContact": (
                x["technical_contact"] if "technical_contact" in x else None
            ),
        }
        for x in result_d
    ]

    return HttpResponse(json.dumps(rows), content_type="application/json")


def publisher_dataset_api(request, pk):
    dataset = []
    org = DatasetOrganization.objects.get(id=pk)

    rows = {
        "name": org.name,
        "description": org.description,
        "administrative_contact": org.administrative_contact,
        "technical_contact": org.technical_contact,
        "country_code": org.country_code,
        "country_or_area": org.country_or_area,
        "installations": org.installations,
        "organization_gbif_uuid": org.organization_gbif_uuid,
    }

    for x in Dataset.objects.filter(organization=pk).all():
        dataset.append(
            {
                "name": x.name,
                "name_zh": x.title,
                "core_type": DATA_MAPPING["publisher_dwc"][x.dwc_core_type],
                "gbif_dataset_uuid": x.organization_uuid,
            }
        )

    rows["dataset"] = dataset

    return HttpResponse(json.dumps(rows), content_type="application/json")


def occurrence_search_v2(request):
    current_path = request.path
    if (
        current_path == "/api/v2/occurrence/search"
        and len(list(request.GET.lists())) == 0
    ):
        init_solr_resp = _get_initial_occurrence_response()
        if init_solr_resp:
            return JsonResponse(init_solr_resp)

    time_start = time.time()
    solr = SolrQuery("taibif_occurrence", request.GET, None)
    req = solr.request()
    resp = solr.get_response()
    if not resp:
        return JsonResponse(
            {
                "results": 0,
                "solr_error_msg": solr.solr_error,
                "solr_url": solr.solr_url,
                "solr_tuples": solr.solr_tuples,
            }
        )

    menus = solr.get_menus()

    query_params = list(request.GET.lists())
    if len(query_params) > 0:
        query_params = [item for item in query_params if item[0] != "q"]
        if query_params:
            last_query_item = query_params[-1][0]
            if last_query_item not in [
                "year",
                "q",
                "taibif_datasetKey",
                "taibif_taxonGroup",
            ]:
                solr = SolrQuery("taibif_occurrence", request.GET, last_query_item)
                last_item_req = solr.request()
                last_item_resp = solr.get_response()
                last_item_menus = solr.get_menus()
                updated_menu = [
                    menu for menu in last_item_menus if menu["key"] == last_query_item
                ]

                updated_menu_index = None
                for i, menu in enumerate(last_item_menus):
                    if menu["key"] == last_query_item:
                        updated_menu_index = i
                        break

                if updated_menu_index is not None:
                    menus[updated_menu_index] = updated_menu[0]
                    resp["menus"] = menus

    if "/api/v1/occurrence/charts" in current_path:
        charts_year = []
        charts_month = []
        charts_dataset = []
        for menu in menus:
            if menu["key"] == "taibif_month":
                charts_month = menu["rows"]
            if menu["key"] == "taibif_year":
                charts_year = menu["rows"]
            if menu["key"] == "taibif_dataset_name_zh":
                charts_dataset = menu["rows"]
        ret = {
            "charts": [
                {
                    "key": "year",
                    "label": "年份",
                    "rows": charts_year,
                },
                {
                    "key": "month",
                    "label": "月份",
                    "rows": charts_month,
                },
                {
                    "key": "dataset",
                    "label": "資料集",
                    "rows": charts_dataset,
                },
            ],
        }
        return JsonResponse(ret)

    # TODO, init taxon_key
    req_dict = dict(request.GET)
    taxon_key = ""
    if tkey := req_dict.get("taxon_key", ""):
        taxon_key = tkey
    # tree
    # treeRoot = Taxon.objects.filter(rank='Kingdom').all()
    # treeData = [{
    #     'id': x.taicol_taxon_id,
    #     'data': {
    #         'name': x.get_name(),
    #         'count': x.count,
    #     },
    # } for x in treeRoot]
    # resp['tree'] = treeData
    resp["tree"] = [
        *OCCURRENCE_ROOT_TREE,
    ]
    # TODO, init taxon_key
    # resp['taxon_checked'] = tkey
    if request.GET.get("debug_solr", ""):
        resp["solr_resp"] = solr.solr_response
        resp["solr_url"] = solr.solr_url
        resp["solr_tuples"] = solr.solr_tuples

    resp["solr_qtime"] = req["solr_response"]["responseHeader"]["QTime"]

    if current_path == "/api/v2/occurrence/map":
        default_solr_count = cache.get("default_solr_count")
        default_map_geojson = cache.get("default_map_geojson")
        solr_updated = (
            False if default_solr_count == resp["count"] else True
        )
        query_params = list(request.GET.lists())
        if len(query_params) > 0:
            solr_url = solr.generate_solr_url(request.GET)
            resp["map_geojson"] = get_geojson(solr_url)
        elif solr_updated or not default_map_geojson:
            # 如果沒有篩選條件且solr資料有更新 或 如果沒有篩選條件且cache沒有default_map_geojson
            resp["map_geojson"] = get_geojson(solr.solr_url)
            cache.set("default_map_geojson", resp["map_geojson"], 2592000)
            cache.set("default_solr_count", resp["count"], 2592000)
        else:  # 如果沒有篩選條件且solr沒更新且cache有default_map_geojson
            resp["map_geojson"] = default_map_geojson

    for menu in menus:
        if menu["key"] == "taibif_year":
            menu["rows"] = [
                {"key": "fake_year_range", "label": "fake_year_range", "count": 0}
            ]
    resp["menus"] = menus
    resp["elapsed"] = time.time() - time_start

    return JsonResponse(resp)


def taxon_tree_node(request, taicol_taxon_id):
    linnaean = request.GET.get("linnaean", "no")

    if linnaean == "yes":
        taxon = Taxon.objects.filter(parent_taxon_id_linnaean=taicol_taxon_id).all()
        children = []
        for taxa in taxon:
            children.append(
                {
                    "id": taxa.taicol_taxon_id,
                    "data": {
                        "name": taxa.get_name(),
                        "count": taxa.count,
                        "rank": taxa.rank,
                    },
                }
            )
        children.sort(key=lambda x: (x["data"]["rank"], x["data"]["name"]))
        parent = Taxon.objects.get(taicol_taxon_id=taicol_taxon_id)
        data = {
            "rank": parent.rank,
            "id": parent.taicol_taxon_id,
            "data": {
                "name": parent.get_name(),
                "count": parent.count,
                "rank": parent.rank,
            },
            "children": children,
        }
    else:
        taxon = Taxon.objects.get(taicol_taxon_id=taicol_taxon_id)
        children = sorted(
            [
                {
                    "id": x.taicol_taxon_id,
                    "data": {
                        "name": x.get_name(),
                        "count": x.count,
                        "rank": x.rank,
                    },
                }
                for x in taxon.children
            ],
            key=lambda x: x["data"]["rank"],
        )

        data = {
            "rank": taxon.rank,
            "id": taxon.taicol_taxon_id,
            "data": {
                "name": taxon.get_name(),
                "count": taxon.count,
                "rank": taxon.rank,
            },
            "children": children,
        }
    # return HttpResponse(json.dumps(data), content_type="application/json")
    return HttpResponse(json.dumps(data), content_type="application/json")


def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def str_to_int(value):
    try:
        float_value = float(value)
        if float_value.is_integer():
            return int(float_value)
        else:
            return None
    except (ValueError, TypeError):
        return None


def is_valid_date(date_string):
    try:
        datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_int(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_float(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_year(year_value, max_year):
    if 1700 <= int(year_value) <= max_year:
        return True
    else:
        return False


def is_valid_month(month_value):
    if 1 <= int(month_value) <= 12:
        return True
    else:
        return False


def validate_params(params):
    """
    驗證 api 傳入的參數是否正確
    """
    if "basisOfRecord" in params:
        CONTROLLED_VOCAB = [
            "材料實體",
            "保存標本",
            "化石標本",
            "活體標本",
            "人為觀測",
            "材料樣本",
            "機器觀測",
            "調查活動",
            "名錄/分類群",
            "出現紀錄",
            "文獻紀錄",
        ]
        if params["basisOfRecord"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. BasisOfRecord must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "kingdom" in params:
        CONTROLLED_VOCAB = [
            "Animalia",
            "Archaea",
            "Bacteria",
            "Chromista",
            "Fungi",
            "Plantae",
            "Protozoa",
            "Viruses",
        ]
        if params["kingdom"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. Kingdom must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "taxonGroup" in params:
        CONTROLLED_VOCAB = [
            "Fishes",
            "Insects",
            "Amphibia",
            "Reptiles",
            "Birds",
            "Mammals",
            "Others",
            "Viruses",
            "Plants",
            "Fungi",
            "Bacteria",
            "Archaea",
        ]
        if params["taxonGroup"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. TaxonGroup must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "establishmentMeans" in params:
        CONTROLLED_VOCAB = [
            "原生",
            "原生：再引進",
            "引進（外來、非原生、非原住）",
            "引進（協助拓殖）",
            "流浪的",
            "不確定的（未知、隱源性）",
        ]
        if params["establishmentMeans"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. EstablishmentMeans must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "occurrenceStatus" in params:
        CONTROLLED_VOCAB = ["出現", "未出現"]
        if params["occurrenceStatus"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. OccurrenceStatus must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "eventDate" in params:
        event_date_list = params["eventDate"].split(",")
        if len(event_date_list) == 2:
            # 區間查詢
            start_date, end_date = event_date_list
            if not is_valid_date(start_date) or not is_valid_date(end_date):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. EventDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        elif len(event_date_list) == 1:
            # 單個日期查詢
            if not is_valid_date(params["eventDate"]):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. EventDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        else:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. EventDate must follow specific format and pattern.",
                    },
                    "params": params,
                }
            )
    if "year" in params:
        max_year = datetime.datetime.now().year
        year_list = params["year"].split(",")
        if len(year_list) == 2:
            # 區間查詢
            start_year, end_year = year_list
            if not is_valid_int(start_year) or not is_valid_int(end_year):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": f"Invalid parameter. Year must be an integar.",
                        },
                        "params": params,
                    }
                )
            if not is_valid_year(start_year, max_year) or not is_valid_year(
                end_year, max_year
            ):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": f"Invalid parameter. Year must range from 1700 to {max_year}.",
                        },
                        "params": params,
                    }
                )
        elif len(year_list) == 1:
            # 單個年份查詢
            if not is_valid_int(params["year"]):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": f"Invalid parameter. Year must be an integar.",
                        },
                        "params": params,
                    }
                )
            if not is_valid_year(params["year"], max_year):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": f"Invalid parameter. Year must range from 1700 to {max_year}.",
                        },
                        "params": params,
                    }
                )
    if "month" in params:
        if not is_valid_int(params["month"]):
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": f"Invalid parameter. Month must be an integar.",
                    },
                    "params": params,
                }
            )
        if not is_valid_month(params["month"]):
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. Month must range from 1 to 12.",
                    },
                    "params": params,
                }
            )
    if "taibifModifiedDate" in params:
        event_date_list = params["taibifModifiedDate"].split(",")
        if len(event_date_list) == 2:
            # 區間查詢
            start_date, end_date = event_date_list
            if not is_valid_date(start_date) or not is_valid_date(end_date):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. TaibifModifiedDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        elif len(event_date_list) == 1:
            # 單個日期查詢
            if not is_valid_date(params["taibifModifiedDate"]):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. TaibifModifiedDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        else:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. TaibifModifiedDate must follow specific format and pattern.",
                    },
                    "params": params,
                }
            )
    if "county" in params:
        CONTROLLED_VOCAB = [
            "Keelung City",
            "New Taipei City",
            "Taipei City",
            "Taoyuan City",
            "Hsinchu County",
            "Hsinchu City",
            "Miaoli County",
            "Taichung City",
            "Changhua County",
            "Nantou County",
            "Yunlin County",
            "Chiayi County",
            "Chiayi City",
            "Tainan City",
            "Kaohsiung City",
            "Pingtung County",
            "Yilan County",
            "Hualien County",
            "Taitung County",
            "Penghu County",
            "Kinmen County",
            "Lienchiang County",
        ]
        if params["county"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. County must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "selfProduced" in params:
        CONTROLLED_VOCAB = ["True", "False"]
        if params["selfProduced"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. SelfProduced must be either True or False",
                    },
                    "params": params,
                }
            )
    if "license" in params:
        CONTROLLED_VOCAB = ["CC0", "CC-BY", "CC-BY-NC", "NA"]
        if params["license"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. License must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "source" in params:
        CONTROLLED_VOCAB = ["TaiBIF IPT", "GBIF"]
        if params["source"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. Source must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "core" in params:
        CONTROLLED_VOCAB = ["SAMPLINGEVENT", "OCCURRENCE", "CHECKLIST", "METADATA"]
        if params["core"] not in CONTROLLED_VOCAB:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. Core must be a controlled vocabulary",
                    },
                    "params": params,
                }
            )
    if "datasetModifiedDate" in params:
        event_date_list = params["datasetModifiedDate"].split(",")
        if len(event_date_list) == 2:
            # 區間查詢
            start_date, end_date = event_date_list
            if not is_valid_date(start_date) or not is_valid_date(end_date):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. DatasetModifiedDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        elif len(event_date_list) == 1:
            # 單個日期查詢
            if not is_valid_date(params["datasetModifiedDate"]):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. DatasetModifiedDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        else:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. DatasetModifiedDate must follow specific format and pattern.",
                    },
                    "params": params,
                }
            )
    if "publicationDate" in params:
        event_date_list = params["publicationDate"].split(",")
        if len(event_date_list) == 2:
            # 區間查詢
            start_date, end_date = event_date_list
            if not is_valid_date(start_date) or not is_valid_date(end_date):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. PublicationDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        elif len(event_date_list) == 1:
            # 單個日期查詢
            if not is_valid_date(params["publicationDate"]):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. PublicationDate must be in valid yyyy-mm-dd format.",
                        },
                        "params": params,
                    }
                )
        else:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. PublicationDate must follow specific format and pattern.",
                    },
                    "params": params,
                }
            )
    if "countryCode" in params:
        pattern = r"^[A-Z]{2}$"
        if not bool(re.match(pattern, params["countryCode"])):
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. CountryCode must follow ISO 3166-1 alpha-2 format.",
                    },
                    "params": params,
                }
            )
    if "boundedBy" in params:
        location_list = params["boundedBy"].split(",")
        # 合理參數：最小經度,最小緯度,最大經度,最大緯度

        if len(location_list) == 4:
            min_lon, min_lat, max_lon, max_lat = location_list

            # 檢查經度是否都是浮點數
            if not (
                is_valid_float(min_lon)
                and is_valid_float(min_lat)
                and is_valid_float(max_lon)
                and is_valid_float(max_lat)
            ):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. Longitude and latitude must be valid decimal numbers.",
                        },
                        "params": params,
                    }
                )

            # 檢查最小經度是否小於最大經度
            if float(min_lon) > float(max_lon):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. minLongitude must be less than maxLongitude.",
                        },
                        "params": params,
                    }
                )
            else:
                # 檢查經度是否在合理範圍內
                if not (
                    (-180 <= float(min_lon) <= 180) and (-180 <= float(max_lon) <= 180)
                ):
                    return JsonResponse(
                        {
                            "status": {
                                "code": 400,
                                "message": "Invalid parameter. Longitude must range from -180 to 180.",
                            },
                            "params": params,
                        }
                    )
            # 檢查最小緯度是否小於最大緯度
            if float(min_lat) > float(max_lat):
                return JsonResponse(
                    {
                        "status": {
                            "code": 400,
                            "message": "Invalid parameter. minLatitude must be less than maxLatitude.",
                        },
                        "params": params,
                    }
                )
            else:
                # 檢查緯度是否在合理範圍內
                if not (
                    (-90 <= float(min_lat) <= 90) and (-90 <= float(max_lat) <= 90)
                ):
                    return JsonResponse(
                        {
                            "status": {
                                "code": 400,
                                "message": "Invalid parameter. Latitude must range from -90 to 90.",
                            },
                            "params": params,
                        }
                    )
        else:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. BoundedBy must follow specific format and pattern.",
                    },
                    "params": params,
                }
            )

    return None


def build_solr_query(params):
    """處理 solr 中和 q 有關的參數，直接轉換成 solr 查詢的語法並合併"""
    filters = []

    ### 物種資訊
    if "originalOccurrenceID" in params:
        filters.append(f'occurrenceID:{params["originalOccurrenceID"]}')
    if "taibifOccurrenceID" in params:
        filters.append(f'taibif_occ_id:{params["taibifOccurrenceID"]}')
    if "basisOfRecord" in params:
        filters.append(f'taibif_basisOfRecord:"{params["basisOfRecord"]}"')
    if "taibifScientificName" in params:
        filters.append(f'taibif_scientificName:{params["taibifScientificName"]}')
    if "taxonRank" in params:
        filters.append(f'taibif_taxonRank:{params["taxonRank"]}')
    if "kingdom" in params:
        filters.append(f'taibif_kingdom:{params["kingdom"]}')
    if "phylum" in params:
        filters.append(f'taibif_phylum:{params["phylum"]}')
    if "class" in params:
        filters.append(f'taibif_class:{params["class"]}')
    if "family" in params:
        filters.append(f'taibif_family:{params["family"]}')
    if "genus" in params:
        filters.append(f'taibif_genus:{params["genus"]}')
    if "taxonGroup" in params:
        filters.append(f'taibif_taxonGroup:{params["taxonGroup"]}')
    if "establishmentMeans" in params:
        filters.append(f'taibif_establishmentMeans:"{params["establishmentMeans"]}"')
    if "occurrenceStatus" in params:
        filters.append(f'taibif_occurrenceStatus:{params["occurrenceStatus"]}')
    ### 時間資訊
    if "eventDate" in params:
        if "," in params["eventDate"]:
            start_date = params["eventDate"].split(",")[0]
            end_date = params["eventDate"].split(",")[1]
            filters.append(f"taibif_eventDate:[{start_date} TO {end_date}]")
        else:
            filters.append(f'taibif_eventDate:[{params["eventDate"]} TO * ]')
    if "year" in params:
        if "," in params["year"]:
            start_year = params["year"].split(",")[0]
            end_year = params["year"].split(",")[1]
            filters.append(f"taibif_year:[{start_year} TO {end_year}]")
        else:
            filters.append(f'taibif_year:[{params["year"]} TO * ]')
    if "month" in params:
        if "," in params["month"]:
            start_month = params["month"].split(",")[0]
            end_month = params["month"].split(",")[1]
            filters.append(f"taibif_month:[{start_month} TO {end_month}]")
        else:
            filters.append(f'taibif_month:[{params["month"]} TO * ]')
    if "taibifModifiedDate" in params:
        if "," in params["taibifModifiedDate"]:
            start_date = params["taibifModifiedDate"].split(",")[0]
            end_date = params["taibifModifiedDate"].split(",")[1]
            filters.append(f"taibif_lastInterpreted:[{start_date} TO {end_date}]")
        else:
            filters.append(
                f'taibif_lastInterpreted:[{params["taibifModifiedDate"]} TO * ]'
            )
    ### 地理資訊
    if "country" in params:
        filters.append(f'taibif_country:{params["country"]}')
    if "county" in params:
        # 有可能有會空格的參數內容要用 "" 包起來
        county_list = params["county"].split(",")
        if len(county_list) > 1:
            county_multi_filters = " OR ".join(
                [f'"{county}"' for county in county_list]
            )
            filters.append(f"taibif_county:({county_multi_filters})")
        else:
            filters.append(f'taibif_county:"{params["county"]}"')
    if "coordinateUncertaintyInMeters" in params:
        filters.append(
            f'taibif_coordinateUncertaintyInMeters:[* TO {params["coordinateUncertaintyInMeters"]}]'
        )
    ### 其他資訊
    if "selfProduced" in params:
        filters.append(f'selfProduced:{params["selfProduced"]}')
    if "license" in params:
        # 有可能有特殊字元的參數內容要用 "" 包起來
        MAPPING = {
            "CC0": "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "CC-BY": "http://creativecommons.org/licenses/by/4.0/legalcode",
            "CC-BY-NC": "http://creativecommons.org/licenses/by-nc/4.0/legalcode",
            "NA": "unknown",
        }
        license_type = MAPPING.get(params["license"])
        filters.append(f'taibif_license:"{license_type}"')
    ### 資料集資訊
    if "taibifDatasetID" in params:
        filters.append(f'taibif_datasetKey:{params["taibifDatasetID"]}')
    if "gbifDatasetID" in params:
        filters.append(f'gbif_datasetKey:{params["gbifDatasetID"]}')
    if "datasetName" in params:
        filters.append(f'taibif_dataset_name_zh:"{params["datasetName"]}"')

    # 沒有提供參數時搜尋所有結果
    if not filters:
        filters.append("*:*")

    return " AND ".join(filters)


def build_solr_spatial_query(params):
    """處理 solr 中和空間搜尋有關的參數，直接轉換成 solr 查詢的語法並合併"""
    filters = []
    if "boundedBy" in params:
        location_list = params["boundedBy"].split(",")
        min_lon, min_lat, max_lon, max_lat = location_list

        lon_list = [float(min_lon), float(max_lon)]
        grid_min_lon = convert_x_coor_to_grid(min(lon_list))
        grid_max_lon = convert_x_coor_to_grid(max(lon_list))
        filters.append(f"{{!frange l={str(grid_min_lon)} u={str(grid_max_lon)}}}grid_x")

        lat_list = [float(min_lat), float(max_lat)]
        grid_min_lat = convert_y_coor_to_grid(min(lat_list))
        grid_max_lat = convert_y_coor_to_grid(max(lat_list))
        filters.append(f"{{!frange l={str(grid_min_lat)} u={str(grid_max_lat)}}}grid_y")

        return filters


def validate_pagination(params):
    """
    rows 預設為 10，最多為 1000
    超過 1000：設為 10
    非正整數：直接返回錯誤
    """
    try:
        rows = int(params.get("rows", 10))
        if rows < 0:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. Rows must be a positive integar",
                    },
                    "params": params,
                }
            )
        rows = min(rows, 1000) if rows > 0 else 10
    except ValueError:
        return JsonResponse(
            {
                "status": {
                    "code": 400,
                    "message": "Invalid parameter. Rows must be a positive integar",
                },
                "params": params,
            }
        )

    """
    offset 預設為 0
    非正整數：直接返回錯誤
    """
    try:
        start = int(params.get("offset", 0))
        if start < 0:
            return JsonResponse(
                {
                    "status": {
                        "code": 400,
                        "message": "Invalid parameter. Start must be a positive integar",
                    },
                    "params": params,
                }
            )
    except ValueError:
        return JsonResponse(
            {
                "status": {
                    "code": 400,
                    "message": "Invalid parameter. Start must be a positive integar",
                },
                "params": params,
            }
        )

    return rows, start


def clean_solr_response(solr_response):
    cleaned_response = []

    for i in solr_response:
        cleaned_response.append(
            {
                ### 物種資訊
                "gbifID": i["gbifID"] if "gbifID" in i else None,
                "originalOccurrenceID": (
                    i["occurrenceID"] if "occurrenceID" in i else None
                ),
                "taibifOccurrenceID": (
                    i["taibif_occ_id"] if "taibif_occ_id" in i else None
                ),
                "basisOfRecord": (
                    i["taibif_basisOfRecord"] if "taibif_basisOfRecord" in i else None
                ),
                "originalScientificName": (
                    i["scientificName"] if "scientificName" in i else None
                ),
                "taibifScientificName": (
                    i["taibif_scientificName"] if "taibif_scientificName" in i else None
                ),
                "taxonRank": i["taibif_taxonRank"] if "taibif_taxonRank" in i else None,
                "scientificNameID": (
                    i["taibif_accepted_namecode"]
                    if "taibif_accepted_namecode" in i
                    else None
                ),
                "taxonBackbone": (
                    i["taibif_taxonBackbone"] if "taibif_taxonBackbone" in i else None
                ),
                "vernacularName": (
                    i["taibif_vernacularName"] if "taibif_vernacularName" in i else None
                ),
                "kingdom": i["taibif_kingdom"] if "taibif_kingdom" in i else None,
                "phylum": i["taibif_phylum"] if "taibif_phylum" in i else None,
                "class": i["taibif_class"] if "taibif_class" in i else None,
                "order": i["taibif_order"] if "taibif_order" in i else None,
                "family": i["taibif_family"] if "taibif_family" in i else None,
                "genus": i["taibif_genus"] if "taibif_genus" in i else None,
                "taxonGroup": (
                    i["taibif_taxonGroup"] if "taibif_taxonGroup" in i else None
                ),
                "establishmentMeans": (
                    i["taibif_establishmentMeans"]
                    if "taibif_establishmentMeans" in i
                    else None
                ),
                "occurrenceStatus": (
                    i["taibif_occurrenceStatus"]
                    if "taibif_occurrenceStatus" in i
                    else None
                ),
                ### 時間資訊
                "eventDate": i["taibif_eventDate"] if "taibif_eventDate" in i else None,
                "year": i["taibif_year"][0] if "taibif_year" in i else None,
                "month": i["taibif_month"][0] if "taibif_month" in i else None,
                "day": i["taibif_day"][0] if "taibif_day" in i else None,
                "taibifModifiedDate": (
                    i["mod_date"][0]
                    if "mod_date" in i
                    else (
                        i["taibif_lastInterpreted"]
                        if "taibif_lastInterpreted" in i
                        else None
                    )
                ),
                ### 地理資訊
                "geodeticDatum": (
                    i["taibif_geodeticDatum"] if "taibif_geodeticDatum" in i else None
                ),
                "verbatimSRS": i["taibif_crs"] if "taibif_crs" in i else None,
                "decimalLongitude": (
                    to_float(i["taibif_decimalLongitude"])
                    if "taibif_decimalLongitude" in i
                    else None
                ),
                "decimalLatitude": (
                    to_float(i["taibif_decimalLatitude"])
                    if "taibif_decimalLatitude" in i
                    else None
                ),
                "coordinatePrecision": (
                    to_float(i["taibif_coordinatePrecision"])
                    if "taibif_coordinatePrecision" in i
                    else None
                ),
                "coordinateUncertaintyInMeters": (
                    to_float(i["taibif_coordinateUncertaintyInMeters"][0])
                    if "taibif_coordinateUncertaintyInMeters" in i
                    else None
                ),
                "dataGeneralizations": (
                    i["dataGeneralizations"] if "dataGeneralizations" in i else None
                ),
                "countryCode": (
                    i["taibif_countryCode"] if "taibif_countryCode" in i else None
                ),
                "country": i["taibif_country"] if "taibif_country" in i else None,
                "county": i["taibif_county"] if "taibif_county" in i else None,
                "locality": i["taibif_locality"] if "taibif_locality" in i else None,
                "habitatReserve": (
                    i["forest_reserves"] if "forest_reserves" in i else None
                ),
                "wildlifeReserve": (
                    i["wildlife_refuges"] if "wildlife_refuges" in i else None
                ),
                ### 其他資訊
                "selfProduced": i["selfProduced"][0] if "selfProduced" in i else None,
                "typeStatus": (
                    i["taibif_typeStatus"] if "taibif_typeStatus" in i else None
                ),
                "recordedBy": (
                    i["taibif_recordedBy"] if "taibif_recordedBy" in i else None
                ),
                "recordNumber": (
                    i["taibif_recordNumber"] if "taibif_recordNumber" in i else None
                ),
                "catalogNumber": i["catalogNumber"] if "catalogNumber" in i else None,
                "license": i["taibif_license"] if "taibif_license" in i else None,
                "organismQuantity": (
                    str_to_int(i["organismQuantity"])
                    if "organismQuantity" in i
                    else None
                ),
                "organismQuantityType": (
                    i["organismQuantityType"] if "organismQuantityType" in i else None
                ),
                "associatedMedia": (
                    i["taibif_mediaReferences"]
                    if "taibif_mediaReferences" in i
                    else None
                ),
                "mediaLicense": (
                    i["taibif_mediaLicense"] if "taibif_mediaLicense" in i else None
                ),
                "issue": i["taibif_issue"] if "taibif_issue" in i else None,
                ### 資料集資訊
                "datasetName": (
                    i["taibif_dataset_name_zh"]
                    if "taibif_dataset_name_zh" in i
                    else None
                ),
                "datasetShortName": (
                    i["taibif_dataset_name"] if "taibif_dataset_name" in i else None
                ),
                "taibifDatasetID": (
                    i["taibif_datasetKey"] if "taibif_datasetKey" in i else None
                ),
                "gbifDatasetID": (
                    i["gbif_datasetKey"] if "gbif_datasetKey" in i else None
                ),
            }
        )

    return cleaned_response


def occurrence_api_v3(request):

    # 只提供有 basisOfRecord 的出現紀錄
    BASE_SOLR_URL = f"http://solr:8983/solr/taibif_occurrence/select?indent=true&q.op=AND&fq=basisOfRecord:*"
    params = request.GET

    # 驗證 q
    validation_response = validate_params(params)
    if validation_response:
        return validation_response  # 參數無效直接回傳錯誤訊息

    # 處理 q
    solr_query = build_solr_query(params)
    spatial_solr_query = build_solr_spatial_query(params)

    # 驗證、處理分頁
    pagination_query = validate_pagination(params)
    if isinstance(pagination_query, JsonResponse):
        return pagination_query

    rows, start = pagination_query

    solr_params = {"q": solr_query, "rows": rows, "start": start, "wt": "json"}

    # print(f'spatial_solr_query: {spatial_solr_query}')

    if spatial_solr_query and len(spatial_solr_query) > 0:
        for filter_condition in spatial_solr_query:
            if "fq" not in solr_params:
                solr_params["fq"] = [filter_condition]
            else:
                solr_params["fq"].append(filter_condition)

    # print(f'solr params: {solr_params}')

    response = requests.get(BASE_SOLR_URL, params=solr_params)
    response.raise_for_status()
    solr_data = response.json()
    cleaned_response = clean_solr_response(solr_data["response"]["docs"])

    api_response = JsonResponse(
        {
            "status": {"code": 200, "message": "Success"},
            "params": params,
            "count": solr_data["response"]["numFound"],
            "data": cleaned_response,
        }
    )

    return api_response


def occurrence_api(request):
    solr_error = ""
    rows = 100
    offset = 0
    fq_query = ""
    fq_list = []
    generate_list = []
    q_list = []
    map_query = ""

    if request.GET.get("q"):
        q_list.append(("q", request.GET.get("q")))
    else:
        q_list.append(("q", "{}:{}".format("*", "*")))

    for key, values in request.GET.lists():
        if key == "start_date" or key == "end_date":
            continue

        # generate search
        elif key == "fl":
            generate_list.append(("fl", values[0]))
        elif key == "wt":
            generate_list.remove(("wt", "json"))
            generate_list.append(("wt", values[0]))
        elif key == "rows":
            rows = int(values[0])
            if rows <= 3000:
                generate_list.append((key, values[0]))
            else:
                rows = 3000
                generate_list.append((key, 3000))
        elif key == "offset":
            offset = values[0]
            generate_list.append(("start", values[0]))

        # fq query
        elif key == "occurrenceID":
            fq_list.append(("fq", '{}:"{}"'.format("occurrenceID", values[0])))
        elif key == "gbifID":
            fq_list.append(("fq", '{}:"{}"'.format("gbifID", values[0])))
        elif key == "taibifOccurrenceID":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_occ_id", values[0])))
        elif key == "basisOfRecord":
            if "," in values[0]:
                vlist = values[0].split(",")
                vlistString = '" OR "'.join(vlist)
                fq_list.append(("fq", f'taibif_basisOfRecord:"{vlistString}"'))
            else:
                fq_list.append(
                    ("fq", "{}:{}".format("taibif_basisOfRecord", values[0]))
                )
        elif key == "datasetName":
            fq_list.append(
                (
                    "fq",
                    "{}:{}".format(
                        "taibif_dataset_name_zh", values[0].replace(":", "\:")
                    ),
                )
            )
        elif key == "occurrenceStatus":
            fq_list.append(
                ("fq", '{}:"{}"'.format("taibif_occurrenceStatus", values[0]))
            )
        elif key == "scientificName":
            fq_list.append(("fq", '(taibif_scientificName:"{}")'.format(values[0])))
        elif key == "taxonRank":
            fq_list.append(("fq", '(taibif_taxonRank:"{}")'.format(values[0])))
        elif key == "taicolTaxonId":
            fq_list.append(("fq", '(taibif_taicolTaxonID:"{}")'.format(values[0])))
        elif key == "kingdom":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_kingdom", values[0])))
        elif key == "phylum":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_phylum", values[0])))
        elif key == "class":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_class", values[0])))
        elif key == "order":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_order", values[0])))
        elif key == "family":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_family", values[0])))
        elif key == "genus":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_genus", values[0])))
        elif key == "taxonGroup":
            if str(values[0]) == "birds":
                fq_list.append(
                    (
                        "fq",
                        "{}:{}".format(
                            "taibif_taxonGroup",
                            "Accipitriformes Anseriformes Apodiformes Bucerotiformes Caprimulgiformes Charadriiformes Ciconiiformes Columbiformes Coraciiformes Cuculiformes Falconiformes Galliformes Gaviiformes Gruiformes Passeriformes Pelecaniformes Phaethontiformes Phoenicopteriformes Piciformes Podicipediformes Procellariiformes Psittaciformes Strigiformes Suliformes Struthioniformes",
                        ),
                    )
                )
            else:
                fq_list.append(("fq", '{}:"{}"'.format("taibif_taxonGroup", values[0])))
        elif key == "country":
            if "," in values[0]:
                vlist = values[0].split(",")
                vlistString = '" OR "'.join(vlist)
                fq_list.append(("fq", f'taibif_country:"{vlistString}"'))
            else:
                fq_list.append(("fq", "{}:{}".format("taibif_country", values[0])))
        elif key == "county":
            if "," in values[0]:
                vlist = values[0].split(",")
                vlistString = '" OR "'.join(vlist)
                fq_list.append(("fq", f'taibif_county:"{vlistString}"'))
            else:
                fq_list.append(("fq", '{}:"{}"'.format("taibif_county", values[0])))
        elif key == "issue":
            if str(values[0]) == "Taxon Match None":
                fq_list.append(("fq", '{}:"{}"'.format("TaxonMatchNone", "true")))
            if str(values[0]) == "Recorded Date Invalid":
                fq_list.append(("fq", '{}:"{}"'.format("RecordedDateInvalid", "true")))
            if str(values[0]) == "Coordinate Invalid":
                fq_list.append(("fq", '{}:"{}"'.format("CoordinateInvalid", "true")))

        elif key == "typeStatus":
            fq_list.append(
                (
                    "fq",
                    "{}:{} -typeStatus:*voucher*".format(
                        "typeStatus", "*" + values[0] + "*"
                    ),
                )
            )
        # range query
        elif key == "modifiedDate":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    (
                        "fq",
                        f"modifiedDate:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]",
                    )
                )
            else:
                fq_list.append(("fq", f'modifiedDate:"{values[0]}T00:00:00Z"'))
        elif key == "taibifModifiedDate":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    ("fq", f"mod_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]")
                )
            else:
                fq_list.append(("fq", f'mod_date:"{values[0]}T00:00:00Z"'))
        elif key == "gbifDatasetID":
            if values[0]:
                fq_list.append(
                    (
                        "fq",
                        '(taibif_datasetKey:"{}" OR gbif_datasetKey:"{}")'.format(
                            values[0], values[0]
                        ),
                    )
                )
            else:
                fq_list.append(("fq", "{}:{}".format("gbif_datasetKey", "*")))
        elif key == "eventDate":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    (
                        "fq",
                        f"taibif_event_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]",
                    )
                )
            else:
                fq_list.append(("fq", f"taibif_event_date:{values[0]}"))
        elif key == "year":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(("fq", f"taibif_year:[{vlist[0]} TO {vlist[1]}]"))
            else:
                fq_list.append(("fq", "{}:{}".format("taibif_year", values[0])))

        elif key == "month":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(("fq", f"taibif_month:[{vlist[0]} TO {vlist[1]}]"))
            else:
                fq_list.append(("fq", '{}:"{}"'.format("taibif_month", values[0])))
        elif key == "decimalLatitude":
            coor_list = [float(c) for c in values]
            y1 = convert_y_coor_to_grid(min(coor_list))
            y2 = convert_y_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
            fq_list.append(("fq", map_query))
        elif key == "decimalLongitude":
            coor_list = [float(c) for c in values]
            x1 = convert_x_coor_to_grid(min(coor_list))
            x2 = convert_x_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"
            fq_list.append(("fq", map_query))
        elif key == "coordinateUncertaintyInMeters":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    (
                        "fq",
                        f"taibif_coordinateUncertaintyInMeters:[{vlist[0]} TO {vlist[1]}]",
                    )
                )
            else:
                fq_list.append(
                    (
                        "fq",
                        "{}:{}".format(
                            "taibif_coordinateUncertaintyInMeters", values[0]
                        ),
                    )
                )
        elif key == "license":
            litype = ""
            if values[0] == "CC-BY":
                litype = "Creative Commons Attribution (CC-BY) 4.0 License"
            elif values[0] == "CC-BY-NC":
                litype = (
                    "Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0 License"
                )
            elif values[0] == "CC0":
                litype = "Public Domain (CC0 1.0)"
            elif values[0] == "NA":
                litype = "unknown"
                # fq_list.append(('fq', '-license:[* TO *]'))
                # continue
            fq_list.append(("fq", '{}:"{}"'.format("license", litype)))
        elif key == "taibifDatasetID":
            fq_list.append(("fq", '(taibif_datasetKey:"{}")'.format(values[0])))

        elif key == "selfProduced":
            fq_list.append(("fq", "{}:{}".format("selfProduced", values[0])))
        else:
            return JsonResponse(
                {
                    "results": 0,
                    "query_column": key,
                    "error_msg": "the column can't be search in this mode.",
                }
            )

    if "rows" not in generate_list:
        generate_list.append(("rows", 100))

    solr = SolrQuery("taibif_occurrence")
    fq_query = urllib.parse.urlencode(fq_list)
    q_query = urllib.parse.urlencode(q_list)
    generate_query = urllib.parse.urlencode(generate_list)

    solr.solr_url = f"http://solr:8983/solr/{solr.core}/select?indent=true&q.op=OR"
    if generate_query:
        solr.solr_url = solr.solr_url + f"&{generate_query}"
    if q_query:
        solr.solr_url = solr.solr_url + f"&{q_query}"
    if fq_query:
        solr.solr_url = solr.solr_url + f"&{fq_query}"

    try:
        resp = urllib.request.urlopen(solr.solr_url)
        resp_dict = resp.read().decode()
        solr.solr_response = json.loads(resp_dict)
    except urllib.request.HTTPError as e:
        solr_error = str(e)

    if not solr.solr_response["response"]["docs"]:
        if solr_error:
            return JsonResponse(
                {
                    "results": 0,
                    "query_list": fq_list,
                    "error_url": solr.solr_url,
                    "error_msg": solr_error,
                }
            )

        if solr.solr_response["response"]["numFound"] == 0:
            res = {}
            res_list = []
            res["count"] = solr.solr_response["response"]["numFound"]
            res["offset"] = int(offset)
            res["rows"] = int(rows)
            res["results"] = res_list
            return JsonResponse(res)

    res = {}
    res_list = []
    for i in solr.solr_response["response"]["docs"]:
        taicolTaxonID = None
        gbifAcceptedID = None
        scientificName = None
        taxonRank = None
        backbone = i["taibif_taxonBackbone"] if "taibif_taxonBackbone" in i else None
        if backbone == "TaiCol" or backbone == "TaiCOL":
            taicolTaxonID = (
                i["taibif_accepted_namecode"]
                if "taibif_accepted_namecode" in i
                else (
                    i["taibif_taicolTaxonID"] if "taibif_taicolTaxonID" in i else None
                )
            )
            gbifAcceptedID = i["taxonKey"] if "taxonKey" in i else None
            scientificName = (
                i["taibif_scientificname"]
                if "taibif_scientificname" in i
                else (
                    i["taibif_scientificName"] if "taibif_scientificName" in i else None
                )
            )
            originalScientificName = (
                i["scientificName"] if "scientificName" in i else None
            )
            taxonRank = i["taibif_taxonRank"] if "taibif_taxonRank" in i else None
        elif backbone == "GBIF":
            gbifAcceptedID = (
                int(float(i["taibif_accepted_namecode"]))
                if "taibif_accepted_namecode" in i
                else None
            )
            scientificName = (
                i["taibif_scientificname"] if "taibif_scientificname" in i else None
            )
            originalScientificName = (
                i["scientificName"] if "scientificName" in i else None
            )
            taxonRank = i["taibif_taxonRank"] if "taibif_taxonRank" in i else None
        elif backbone == None:
            gbifAcceptedID = i["taxonKey"] if "taxonKey" in i else None
            scientificName = ""
            originalScientificName = (
                i["scientificName"] if "scientificName" in i else None
            )
            taxonRank = i["taibif_taxonRank"] if "taibif_taxonRank" in i else None

        issue = None
        if (
            "geo_issue" in i
            and i["geo_issue"]
            or "taxon_issue" in i
            and i["taxon_issue"]
            or "time_issue" in i
        ):
            issue = ";".join(
                filter(
                    None,
                    [i.get("geo_issue"), i.get("taxon_issue"), i.get("time_issue")],
                )
            )

        group = i["taibif_taxonGroup"] if "taibif_taxonGroup" in i else None
        # if 'orderzh' in i :
        #     if i['orderzh'] in ['Accipitriformes','Anseriformes','Apodiformes','Bucerotiformes','Caprimulgiformes','Charadriiformes','Ciconiiformes','Columbiformes','Coraciiformes','Cuculiformes','Falconiformes','Galliformes','Gaviiformes','Gruiformes','Passeriformes','Pelecaniformes','Phaethontiformes','Phoenicopteriformes','Piciformes','Podicipediformes','Procellariiformes','Psittaciformes','Strigiformes','Suliformes','Struthioniformes',]:
        #         group = 'Birds'
        issues = []
        if "TaxonMatchNone" in i and i["TaxonMatchNone"][0] == True:
            issues.append("TaxonMatchNone")
        if "CoordinateInvalid" in i and i["CoordinateInvalid"][0] == True:
            issues.append("CoordinateInvalid")
        if "RecordedDateInvalid" in i and i["RecordedDateInvalid"][0] == True:
            issues.append("RecordedDateInvalid")

        res_list.append(
            {
                # 轉釋資料
                "taibifOccurrenceID": i["taibif_occ_id"],
                "basisOfRecord": (
                    i["taibif_basisOfRecord"] if "taibif_basisOfRecord" in i else None
                ),
                "scientificName": scientificName,
                "originalScientificName": originalScientificName,
                "taxonGroup": group,
                "taxonRank": taxonRank,
                "scientificNameID": (
                    i["taibif_namecode"] if "taibif_namecode" in i else None
                ),
                "isPreferredName": (
                    i["taibif_vernacularName"] if "taibif_vernacularName" in i else None
                ),
                "taxonBackbone": backbone,
                "taicolTaxonID": taicolTaxonID,
                "gbifAcceptedID": gbifAcceptedID,
                "kingdom": i["taibif_kingdom"] if "taibif_kingdom" in i else None,
                "phylum": i["taibif_phylum"] if "taibif_phylum" in i else None,
                "class": i["taibif_class"] if "taibif_class" in i else None,
                "order": i["taibif_order"] if "taibif_order" in i else None,
                "family": i["taibif_family"] if "taibif_family" in i else None,
                "genus": i["taibif_genus"] if "taibif_genus" in i else None,
                "eventDate": i["taibif_eventDate"] if "taibif_eventDate" in i else None,
                "year": i["taibif_year"][0] if "taibif_year" in i else None,
                "month": i["taibif_month"][0] if "taibif_month" in i else None,
                "day": i["taibif_day"][0] if "taibif_day" in i else None,
                "geodeticDatum": (
                    i["taibif_geodeticDatum"] if "taibif_geodeticDatum" in i else None
                ),  # 對到verbatimCoordinateSystem
                "verbatimSRS": (
                    i["taibif_crs"] if "taibif_crs" in i else None
                ),  # verbatimSRS
                "decimalLongitude": (
                    str(i["taibif_longitude"][0])
                    if "taibif_longitude" in i
                    else (
                        i["taibif_decimalLongitude"]
                        if "taibif_decimalLongitude" in i
                        else None
                    )
                ),
                "decimalLatitude": (
                    str(i["taibif_latitude"][0])
                    if "taibif_latitude" in i
                    else (
                        i["taibif_decimalLatitude"]
                        if "taibif_decimalLatitude" in i
                        else None
                    )
                ),
                "coordinateUncertaintyInMeters": (
                    i["taibif_coordinateUncertaintyInMeters"][0]
                    if "taibif_coordinateUncertaintyInMeters" in i
                    else None
                ),
                "countryCode": (
                    i["taibif_countryCode"] if "taibif_countryCode" in i else None
                ),
                "country": i["taibif_country"] if "taibif_country" in i else None,
                "county": i["taibif_county"] if "taibif_county" in i else None,
                "habitatReserve": (
                    i["forestN"][0]
                    if "forestN" in i
                    else (i["forest_reserves"] if "forest_reserves" in i else None)
                ),
                "wildlifeReserve": (
                    i["wildlifeN"][0]
                    if "wildlifeN" in i
                    else (i["wildlife_refuges"] if "wildlife_refuges" in i else None)
                ),
                "occurrenceStatus": (
                    i["taibif_occurrenceStatus"]
                    if "taibif_occurrenceStatus" in i
                    else None
                ),
                "selfProduced": i["selfProduced"][0],
                "license": (
                    i["taibif_license"]
                    if "taibif_license" in i and i["taibif_license"] != "unknown"
                    else "NA"
                ),
                # 基本資料
                "datasetName": (
                    i["taibif_dataset_name_zh"]
                    if "taibif_dataset_name_zh" in i
                    else None
                ),
                "datasetShortName": (
                    i["taibif_dataset_name"] if "taibif_dataset_name" in i else None
                ),
                "occurrenceID": i["occurrenceID"] if "occurrenceID" in i else None,
                "catalogNumber": i["catalogNumber"] if "catalogNumber" in i else None,
                "taibifCreatedDate": i["mod_date"][0] if "mod_date" in i else None,
                "taibifModifiedDate": (
                    i["mod_date"][0]
                    if "mod_date" in i
                    else (
                        i["taibif_lastInterpreted"]
                        if "taibif_lastInterpreted" in i
                        else None
                    )
                ),
                "dataGeneralizations": (
                    i["dataGeneralizations"] if "dataGeneralizations" in i else None
                ),
                "coordinatePrecision": (
                    i["taibif_coordinatePrecision"]
                    if "taibif_coordinatePrecision" in i
                    else None
                ),
                "locality": i["locality"] if "locality" in i else None,
                "preservation": i["preservation"] if "preservation" in i else None,
                "typeStatus": (
                    i["typeStatus"]
                    if "typeStatus" in i
                    else (i["taibif_typeStatus"] if "taibif_typeStatus" in i else None)
                ),
                "recordedBy": i["recordedBy"] if "recordedBy" in i else None,
                "recordNumber": i["recordNumber"] if "recordNumber" in i else None,
                "organismQuantity": (
                    i["organismQuantity"] if "organismQuantity" in i else None
                ),
                "organismQuantityType": (
                    i["organismQuantityType"] if "organismQuantityType" in i else None
                ),
                "associatedMedia": (
                    i["taibif_mediaReferences"]
                    if "taibif_mediaReferences" in i
                    else (i["mediaReferences"] if "mediaReferences" in i else None)
                ),
                "mediaLicense": (
                    i["taibif_mediaLicense"] if "taibif_mediaLicense" in i else None
                ),
                # 常用資料
                "gbifID": i["gbifID"] if "gbifID" in i else None,
                "taibifDatasetID": (
                    i["taibifDatasetID"]
                    if "taibifDatasetID" in i
                    else (i["taibif_datasetKey"] if "taibif_datasetKey" in i else None)
                ),
                "gbifDatasetID": (
                    i["gbif_datasetKey"] if "gbif_datasetKey" in i else None
                ),
                "establishmentMeans": (
                    i["establishmentMeans"]
                    if "establishmentMeans" in i
                    else (
                        i["taibif_establishmentMeans"]
                        if "taibif_establishmentMeans" in i
                        else None
                    )
                ),
                "issue": ",".join(issues) if issues else (issue if issue else None),
                # 沒分類
                # 'modifiedDate':i['modified'] if 'modified' in i else None,
            }
        )

    res["url"] = solr.solr_url
    res["count"] = solr.solr_response["response"]["numFound"]
    res["offset"] = int(offset)
    res["rows"] = int(rows)
    res["results"] = res_list
    return JsonResponse(res)


def raw_occ_api(request):
    solr_error = ""
    rows = 100
    offset = 0
    fq_query = ""
    fq_list = []
    generate_list = []
    q_list = []
    map_query = ""

    if request.GET.get("q"):
        q_list.append(("q", request.GET.get("q")))
    else:
        q_list.append(("q", "{}:{}".format("*", "*")))

    for key, values in request.GET.lists():
        if key == "start_date" or key == "end_date":
            continue

        # generate search
        elif key == "fl":
            generate_list.append(("fl", values[0]))
        elif key == "wt":
            generate_list.remove(("wt", "json"))
            generate_list.append(("wt", values[0]))
        elif key == "rows":
            rows = int(values[0])
            if rows <= 3000:
                generate_list.append((key, values[0]))
            else:
                rows = 3000
                generate_list.append((key, 3000))
        elif key == "offset":
            offset = values[0]
            generate_list.append(("start", values[0]))

        # fq query
        elif key == "occurrenceID":
            fq_list.append(("fq", '{}:"{}"'.format("occurrenceID", values[0])))
        elif key == "taibifOccurrenceID":
            fq_list.append(("fq", '{}:"{}"'.format("taibif_occ_id", values[0])))
        elif key == "basisOfRecord":
            if "," in values[0]:
                vlist = values[0].split(",")
                vlistString = '" OR "'.join(vlist)
                fq_list.append(("fq", f'taibif_basisOfRecord:"{vlistString}"'))
            else:
                fq_list.append(
                    ("fq", "{}:{}".format("taibif_basisOfRecord", values[0]))
                )
        elif key == "datasetName":
            fq_list.append(
                (
                    "fq",
                    "{}:{}".format(
                        "taibif_dataset_name_zh", values[0].replace(":", "\:")
                    ),
                )
            )
        elif key == "occurrenceStatus":
            fq_list.append(
                ("fq", '{}:"{}"'.format("taibif_occurrenceStatus", values[0]))
            )
        elif key == "scientificName":
            fq_list.append(("fq", "{}:{}".format("taibif_scientificname", values[0])))
        elif key == "taxonRank":
            fq_list.append(("fq", '{}:"{}"'.format("taxon_rank", values[0])))
        elif key == "taicolTaxonId":
            fq_list.append(("fq", '{}:"{}"'.format("taicol_taxon_id", values[0])))
        elif key == "kingdom":
            fq_list.append(("fq", '{}:"{}"'.format("kingdomzh", values[0])))
        elif key == "phylum":
            fq_list.append(("fq", '{}:"{}"'.format("phylumzh", values[0])))
        elif key == "class":
            fq_list.append(("fq", '{}:"{}"'.format("classzh", values[0])))
        elif key == "order":
            fq_list.append(("fq", '{}:"{}"'.format("orderzh", values[0])))
        elif key == "family":
            fq_list.append(("fq", '{}:"{}"'.format("familyzh", values[0])))
        elif key == "genus":
            fq_list.append(("fq", '{}:"{}"'.format("genuszh", values[0])))
        elif key == "taxonGroup":
            if str(values[0]) == "birds":
                fq_list.append(
                    (
                        "fq",
                        "{}:{}".format(
                            "taibif_taxonGroup",
                            "Accipitriformes Anseriformes Apodiformes Bucerotiformes Caprimulgiformes Charadriiformes Ciconiiformes Columbiformes Coraciiformes Cuculiformes Falconiformes Galliformes Gaviiformes Gruiformes Passeriformes Pelecaniformes Phaethontiformes Phoenicopteriformes Piciformes Podicipediformes Procellariiformes Psittaciformes Strigiformes Suliformes Struthioniformes",
                        ),
                    )
                )
            else:
                fq_list.append(("fq", '{}:"{}"'.format("taibif_taxonGroup", values[0])))
        elif key == "country":
            if "," in values[0]:
                vlist = values[0].split(",")
                vlistString = '" OR "'.join(vlist)
                fq_list.append(("fq", f'taibif_country:"{vlistString}"'))
            else:
                fq_list.append(("fq", "{}:{}".format("taibif_country", values[0])))
        elif key == "county":
            if "," in values[0]:
                vlist = values[0].split(",")
                vlistString = '" OR "'.join(vlist)
                fq_list.append(("fq", f'taibif_county:"{vlistString}"'))
            else:
                fq_list.append(("fq", '{}:"{}"'.format("taibif_county", values[0])))
        elif key == "issue":
            if str(values[0]) == "Taxon Match None":
                fq_list.append(("fq", '{}:"{}"'.format("TaxonMatchNone", "true")))
            if str(values[0]) == "Recorded Date Invalid":
                fq_list.append(("fq", '{}:"{}"'.format("RecordedDateInvalid", "true")))
            if str(values[0]) == "Coordinate Invalid":
                fq_list.append(("fq", '{}:"{}"'.format("CoordinateInvalid", "true")))

        elif key == "taibifDatasetID":
            fq_list.append(("fq", '{}:"{}"'.format("taibifDatasetID", values[0])))

        elif key == "typeStatus":
            fq_list.append(
                (
                    "fq",
                    "{}:{} -typeStatus:*voucher*".format(
                        "typeStatus", "*" + values[0] + "*"
                    ),
                )
            )
        # range query
        elif key == "modifiedDate":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    (
                        "fq",
                        f"modifiedDate:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]",
                    )
                )
            else:
                fq_list.append(("fq", f'modifiedDate:"{values[0]}T00:00:00Z"'))
        elif key == "taibifModifiedDate":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    ("fq", f"mod_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]")
                )
            else:
                fq_list.append(("fq", f'mod_date:"{values[0]}T00:00:00Z"'))
        elif key == "gbifDatasetID":
            if values[0]:
                fq_list.append(("fq", '{}:"{}"'.format("gbif_datasetKey", values[0])))
            else:
                fq_list.append(("fq", "{}:{}".format("gbif_datasetKey", "*")))
        elif key == "eventDate":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    (
                        "fq",
                        f"taibif_event_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]",
                    )
                )
            else:
                fq_list.append(("fq", f"taibif_event_date:{values[0]}"))
        elif key == "year":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(("fq", f"taibif_year:[{vlist[0]} TO {vlist[1]}]"))
            else:
                fq_list.append(("fq", "{}:{}".format("taibif_year", values[0])))

        elif key == "month":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(("fq", f"taibif_month:[{vlist[0]} TO {vlist[1]}]"))
            else:
                fq_list.append(("fq", '{}:"{}"'.format("taibif_month", values[0])))
        elif key == "decimalLatitude":
            coor_list = [float(c) for c in values]
            y1 = convert_y_coor_to_grid(min(coor_list))
            y2 = convert_y_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
            fq_list.append(("fq", map_query))
        elif key == "decimalLongitude":
            coor_list = [float(c) for c in values]
            x1 = convert_x_coor_to_grid(min(coor_list))
            x2 = convert_x_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"
            fq_list.append(("fq", map_query))
        elif key == "coordinateUncertaintyInMeters":
            if "," in values[0]:
                vlist = values[0].split(",")
                fq_list.append(
                    (
                        "fq",
                        f"taibif_coordinateUncertaintyInMeters:[{vlist[0]} TO {vlist[1]}]",
                    )
                )
            else:
                fq_list.append(
                    (
                        "fq",
                        "{}:{}".format(
                            "taibif_coordinateUncertaintyInMeters", values[0]
                        ),
                    )
                )
        elif key == "license":
            litype = ""
            if values[0] == "CC-BY":
                litype = "Creative Commons Attribution (CC-BY) 4.0 License"
            elif values[0] == "CC-BY-NC":
                litype = (
                    "Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0 License"
                )
            elif values[0] == "CC0":
                litype = "Public Domain (CC0 1.0)"
            elif values[0] == "NA":
                litype = "unknown"
                # fq_list.append(('fq', '-license:[* TO *]'))
                # continue
            fq_list.append(("fq", '{}:"{}"'.format("license", litype)))

        elif key == "establishmentMeans":
            fq_list.append(("fq", "{}:{}".format("establishmentMeans", values[0])))

        elif key == "selfProduced":
            fq_list.append(("fq", "{}:{}".format("selfProduced", values[0])))
        else:
            return JsonResponse(
                {
                    "results": 0,
                    "query_column": key,
                    "error_msg": "the column can't be search in this mode.",
                }
            )

    if "rows" not in generate_list:
        generate_list.append(("rows", 100))

    solr = SolrQuery("taibif_occurrence")
    fq_query = urllib.parse.urlencode(fq_list)
    q_query = urllib.parse.urlencode(q_list)
    generate_query = urllib.parse.urlencode(generate_list)

    solr.solr_url = f"http://solr:8983/solr/{solr.core}/select?indent=true&q.op=OR"
    if generate_query:
        solr.solr_url = solr.solr_url + f"&{generate_query}"
    if q_query:
        solr.solr_url = solr.solr_url + f"&{q_query}"
    if fq_query:
        solr.solr_url = solr.solr_url + f"&{fq_query}"

    resp = urllib.request.urlopen(solr.solr_url)
    resp_dict = resp.read().decode()
    solr.solr_response = json.loads(resp_dict)
    if not solr.solr_response["response"]["docs"]:
        if solr_error:
            return JsonResponse(
                {
                    "results": 0,
                    "query_list": fq_list,
                    "error_url": solr.solr_url,
                    "error_msg": solr_error,
                }
            )

        if solr.solr_response["response"]["numFound"] == 0:
            res = {}
            res_list = []
            res["count"] = solr.solr_response["response"]["numFound"]
            res["offset"] = int(offset)
            res["rows"] = int(rows)
            res["results"] = res_list
            return JsonResponse(res)
    return JsonResponse(solr.solr_response)


# @json_ret
def search_dataset(request):
    has_menu = True if request.GET.get("menu", "") else False
    menu_list = []
    # content search
    ds_search = DatasetSearch(list(request.GET.lists()))

    if has_menu:
        condiction_menu = list(request.GET.lists())

        # 發布單位 publisher
        publisher_query = [(k, v) for k, v in condiction_menu if k != "publisher"]
        publisher_count = (
            DatasetSearch(publisher_query)
            .query.values("organization", "organization_name")
            .exclude(organization__isnull=True)
            .exclude(organization_name__isnull=True)
            .annotate(count=Count("*"))
            .order_by("-count")
        )
        publisher_rows = sorted(
            [
                {
                    "key": item["organization"],
                    "label": item["organization_name"],
                    "count": item["count"] or 0,
                }
                for item in publisher_count
            ],
            key=lambda d: d["count"],
            reverse=True,
        )

        # 發布地區/國家 publishing country or area
        country_query = [(k, v) for k, v in condiction_menu if k != "country"]
        country_count_data = (
            DatasetSearch(country_query)
            .query.values("country")
            .exclude(country__exact="")
            .annotate(count=Count("*"))
            .order_by("-count")
        )
        country_rows = sorted(
            [
                {
                    "key": item["country"],
                    "label": DATA_MAPPING["country"].get(item["country"], "未映射國家"),
                    "count": item["count"] or 0,
                }
                for item in country_count_data
            ],
            key=lambda d: d["count"],
            reverse=True,
        )

        # 授權類型 license
        rights_query = [(k, v) for k, v in condiction_menu if k != "rights"]
        rights_count_data = (
            DatasetSearch(rights_query)
            .query.values("data_license")
            .exclude(data_license__exact="")
            .annotate(count=Count("*"))
            .order_by("-count")
        )
        rights_rows = sorted(
            [
                {
                    "key": DATA_MAPPING["rights"].get(
                        item["data_license"], "未映射授權"
                    ),
                    "label": DATA_MAPPING["rights"].get(
                        item["data_license"], "未映射授權"
                    ),
                    "count": item["count"] or 0,
                }
                for item in rights_count_data
            ],
            key=lambda d: d["count"],
            reverse=True,
        )

        # 資料來源 Source
        source_query = [(k, v) for k, v in condiction_menu if k != "source"]
        source_count_data = (
            DatasetSearch(source_query)
            .query.values("source")
            .annotate(count=Count("*"))
            .order_by("-count")
        )
        source_rows = sorted(
            [
                {
                    "key": item["source"],
                    "label": item["source"],
                    "count": item["count"] or 0,
                }
                for item in source_count_data
            ],
            key=lambda d: d["count"],
            reverse=True,
        )

        menu_list = [
            {"key": "publisher", "label": "發布單位 Publisher", "rows": publisher_rows},
            {
                "key": "country",
                "label": "發布地區/國家 Publishing Country or Area",
                "rows": country_rows,
            },
            {"key": "rights", "label": "授權類型 License", "rows": rights_rows},
            {"key": "source", "label": "資料來源 Source", "rows": source_rows},
        ]

    res = ds_search.get_results()
    data = {
        "search": res,
    }
    if has_menu:
        data["menus"] = menu_list

    return HttpResponse(json.dumps(data), content_type="application/json")


# @json_ret
def search_publisher(request):
    has_menu = True if request.GET.get("menu", "") else False
    menu_list = []

    if has_menu:
        country_list = (
            DatasetOrganization.objects.values("country_code")
            .exclude(country_code__isnull=True)
            .annotate(count=Count("country_code"))
            .order_by("-count")
            .all()
        )
        menu_list = [
            {
                "key": "countrycode",
                "label": "國家/區域 Country or Area",
                "rows": [
                    {
                        "label": DATA_MAPPING["country"][x["country_code"]],
                        "count": x["count"],
                        "key": x["country_code"],
                    }
                    for x in country_list
                ],
            },
        ]

        # menus = [
        #     {
        #         'key': 'country_code',
        #         'label': '國家/區域 Country or Area',
        #         'rows': [{'label': DATA_MAPPING['country'][x['country_code']], 'key': x['country_code'], 'count': x['count']} for x in country_list]
        #     },
        # ]

    # search
    publisher_search = PublisherSearch(list(request.GET.lists()))
    res = publisher_search.get_results()

    data = {
        "search": res,
    }

    if has_menu:
        data["menus"] = menu_list

    # return {'data': data }
    return HttpResponse(json.dumps(data), content_type="application/json")


# @json_ret
def search_species(request):
    status = request.GET.get("status", "")
    rank = request.GET.get("rank", "")
    species_search = SpeciesSearch(list(request.GET.lists()))
    # species_ids = list(species_search.query.values('id').all())
    has_menu = True if request.GET.get("menu", "") else False
    menu_list = []

    condiction_menu = list(request.GET.lists())
    # higherTaxon_query = []
    # for k,v in condiction_menu:
    #     if k!= "highertaxon":
    #         higherTaxon_query.append((k,v))
    # higherTaxon_menu = SpeciesSearch(higherTaxon_query)

    # kingdom_count = higherTaxon_menu.query\
    #         .extra(select ={'taxon_id':'kingdom_taxon_id'})\
    #         .values('taxon_id')\
    #         .exclude(kingdom_taxon_id__exact='')\
    #         .annotate(count=Count('kingdom_taxon_id'))\
    #         .order_by('-count')
    # phylum_count = higherTaxon_menu.query\
    #         .extra(select ={'taxon_id':'phylum_taxon_id'})\
    #         .values('taxon_id')\
    #         .exclude(phylum_taxon_id__exact='')\
    #         .annotate(count=Count('phylum_taxon_id'))\
    #         .order_by('-count')
    # order_count = higherTaxon_menu.query\
    #         .extra(select ={'taxon_id':'order_taxon_id'})\
    #         .values('taxon_id')\
    #         .exclude(order_taxon_id__exact='')\
    #         .annotate(count=Count('order_taxon_id'))\
    #         .order_by('-count')
    # class_count = higherTaxon_menu.query\
    #         .extra(select ={'taxon_id':'class_taxon_id'})\
    #         .values('taxon_id')\
    #         .exclude(class_taxon_id__exact='')\
    #         .annotate(count=Count('class_taxon_id'))\
    #         .order_by('-count')
    # family_count = higherTaxon_menu.query\
    #         .extra(select ={'taxon_id':'family_taxon_id'})\
    #         .values('taxon_id')\
    #         .exclude(family_taxon_id__exact='')\
    #         .annotate(count=Count('family_taxon_id'))\
    #         .order_by('-count')
    # genus_count = higherTaxon_menu.query\
    #         .extra(select ={'taxon_id':'genus_taxon_id'})\
    #         .values('taxon_id')\
    #         .exclude(genus_taxon_id__exact='')\
    #         .annotate(count=Count('genus_taxon_id'))\
    #         .order_by('-count')

    # taxon_count = kingdom_count.union(phylum_count).union(order_count).union(class_count).union(family_count).union(genus_count).order_by('-count')[:10]

    # higherTaxon_menu_tmp = []
    # if taxon_count:
    #     higherTaxon_menu_tmp = [{
    #         'key': x['taxon_id'],
    #         'label': Taxon.objects.get(taicol_taxon_id = x['taxon_id']).name,
    #         'count': x['count'],
    #     } for x in taxon_count if x['taxon_id'] != None]

    if has_menu:
        menus = [
            {
                "key": "rank",
                "label": "分類位階 Rank",
                "rows": [
                    {
                        "key": x["key"],
                        "label": x["label"],
                        "count": x["count"],
                    }
                    for x in Taxon.get_tree(rank=rank, status=status)
                ],
            },
            # {
            #     'key': 'highertaxon',
            #     'label': '高階分類群 Higher Taxon Classification',
            #     'rows': higherTaxon_menu_tmp,
            # },
            {
                "key": "status",
                "label": "學名狀態 Status",
                "rows": [
                    {"label": "有效的 Accepted", "key": "accepted"},
                    {"label": "同物異名 Synonym", "key": "synonym"},
                ],
            },
        ]

    # search
    res = species_search.get_results()
    data = {
        "search": res,
    }
    if has_menu:
        data["menus"] = menus

    # return {'data': data }
    return HttpResponse(json.dumps(data), content_type="application/json")


def data_stats(request):
    """for D3 charts"""
    is_most = request.GET.get("most", "")
    current_year = datetime.datetime.now().year

    query = Dataset.objects
    if is_most:
        query = query.filter(is_most_project=True)

    rows = query.filter(status__contains="PUBLIC")
    hdata = {}
    current_year_data = {
        "dataset": [{"x": "{}".format(x), "y": 0} for x in range(1, 13)],
        "occurrence": [{"x": "{}".format(x), "y": 0} for x in range(1, 13)],
    }
    history_data = {"dataset": [], "occurrence": []}
    for i in rows:
        if not i.created:
            continue

        y = str(i.created.year)
        if str(current_year) == y:
            m = i.created.month
            current_year_data["dataset"][m - 1]["y"] += 1
            current_year_data["occurrence"][m - 1]["y"] += i.num_occurrence
        if y not in hdata:
            hdata[y] = {"dataset": 1, "occurrence": i.num_occurrence}
        else:
            hdata[y]["dataset"] += 1
            hdata[y]["occurrence"] += i.num_occurrence

    sorted_year = sorted(hdata)
    accu_ds = 0
    accu_occur = 0
    for y in sorted_year:
        accu_occur += hdata[y]["occurrence"]
        accu_ds += hdata[y]["dataset"]
        history_data["dataset"].append(
            {"year": int(y), "y1": hdata[y]["dataset"], "y2": accu_ds}
        )
        history_data["occurrence"].append(
            {"year": int(y), "y1": hdata[y]["occurrence"], "y2": accu_occur}
        )
    data = {
        "current_year": current_year_data,
        "history": history_data,
    }

    return HttpResponse(json.dumps(data), content_type="application/json")


@json_ret
def species_detail(request, pk):
    taxon = Taxon.objects.get(pk=pk)
    # rows = RawDataOccurrence.objects.values('taibif_dataset_name', 'decimallatitude', 'decimallongitude').filter(scientificname=taxon.name).all()
    scname = "{} {}".format(taxon.parent.name, taxon.name)
    return {"data": {}}


## Kuan-Yu added for API occurence record
def search_occurrence_v1(request):
    year_start = 1000
    year_end = 2021

    solr_q_fq_list = []
    solr_fq = ""
    solr_q_list = []
    solr_q = "*:*"
    for term, values in list(request.GET.lists()):
        if term != "q":
            if term != "menu":
                if term == "year":
                    val = values[0].replace(",", " TO ")
                    solr_q_fq_list.append("{}:[{}]".format(term, val))
                    year_start = values[0].split(",", 1)
                    year_end = values[0].split(",", 2)
                elif term == "dataset":
                    solr_q_fq_list.append(
                        '{}:"{}"'.format(
                            "taibif_dataset_name_zh", '" OR "'.join(values)
                        )
                    )
                elif term == "month":
                    solr_q_fq_list.append("{}:{}".format(term, " OR ".join(values)))

        else:
            solr_q_list.append("{}:{}".format("_text_", " OR ".join(values)))

    if len(solr_q_list) > 0:
        solr_q = " OR ".join(solr_q_list)

    if len(solr_q_fq_list) > 0:
        solr_fq = " OR ".join(solr_q_fq_list)

    menu_year = []
    menu_month = []
    menu_dataset = []
    menu_country = []
    menu_publisher = []

    search_count = 0
    search_limit = 20
    search_offset = 0
    search_results = []
    # publisher_query = Dataset.objects\
    #                         .values('organization','organization_verbatim')\
    #                         .exclude(organization__isnull=True)\
    #                         .annotate(count=Count('organization'))\
    #                         .order_by('-count')
    # menu_publisher = [{
    #    'key':x['organization'],
    #    'label':x['organization_verbatim'],
    #    'count': x['count']
    # } for x in publisher_query]

    time_start = time.time()
    facet_dataset = "dataset:{type:terms,field:taibif_dataset_name_zh}"
    facet_month = "month:{type:range,field:month,start:1,end:13,gap:1}"
    facet_country = "country:{type:terms,field:country,mincount:0,limit:-1}"
    facet_publisher = "publisher:{type:terms,field:publisher}"
    facet_json = (
        "json.facet={"
        + facet_dataset
        + ","
        + facet_month
        + ","
        + facet_country
        + ","
        + facet_publisher
        + "}"
    )
    r = requests.get(
        f"http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=AND&rows={search_limit}&q={solr_q}&fq={solr_fq}&{facet_json}"
    )

    if r.status_code == 200:
        data = r.json()
        search_count = data["response"]["numFound"]
        if search_count != 0:
            search_offset = data["response"]["start"]
            search_results = data["response"]["docs"]
            for i, v in enumerate(search_results):
                ## copy fields
                date = "{}-{}-{}".format(
                    v["year"] if v.get("year", "") else "",
                    v["month"] if v.get("month", "") else "",
                    v["day"] if v.get("day", "") else "",
                )
                search_results[i]["vernacular_name"] = v.get("vernacularName", "")
                search_results[i]["scientific_name"] = v.get("scientificName", "")
                search_results[i]["dataset"] = v["taibif_dataset_name"]
                search_results[i]["date"] = date
                search_results[i]["taibif_id"] = "{}__{}".format(
                    v["taibif_dataset_name"], v["_version_"]
                )
                search_results[i]["kingdom"] = v.get("kingdom_zh", "")
                search_results[i]["phylum"] = v.get("phylum_zh", "")
                search_results[i]["class"] = v.get("class_zh", "")
                search_results[i]["order"] = v.get("order_zh", "")
                search_results[i]["family"] = v.get("family_zh", "")
                search_results[i]["genus"] = v.get("genus_zh", "")
                search_results[i]["species"] = v.get("species_zh", "")

            menu_year = [
                {
                    "key": 0,
                    "label": 0,
                    "count": 0,
                    "year_start": year_start,
                    "year_end": year_end,
                }
            ]
            menu_month = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["month"]["buckets"]
            ]
            menu_dataset = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["dataset"]["buckets"]
            ]
            menu_country = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["country"]["buckets"]
            ]
            menu_publisher = [
                {"key": x["val"], "label": x["val"], "count": x["count"]}
                for x in data["facets"]["publisher"]["buckets"]
            ]
        else:
            menu_year = [
                {
                    "key": 0,
                    "label": 0,
                    "count": 0,
                    "year_start": year_start,
                    "year_end": year_end,
                }
            ]
            menu_month = [{"key": x, "label": x, "count": 0} for x in range(12)]
            menu_dataset = [{"key": 0, "label": 0, "count": 0}]
            menu_country = [{"key": 0, "label": 0, "count": 0}]
            menu_publisher = [{"key": 0, "label": 0, "count": 0}]

        # search_limit = 20

    ret = {
        "menus": [
            {
                "key": "country",  #'countrycode',
                "label": "國家/區域",
                "rows": menu_country,
            },
            {
                "key": "year",
                "label": "年份",
                "rows": menu_year,
            },
            {
                "key": "month",
                "label": "月份",
                "rows": menu_month,
            },
            {
                "key": "dataset",
                "label": "資料集",
                "rows": menu_dataset,
            },
            {
                "key": "publisher",
                "label": "發布單位",
                "rows": menu_publisher,
            },
        ],
        "search": {
            "elapsed": time.time() - time_start,
            "results": search_results,
            "offset": search_offset,
            "limit": search_limit,
            "count": search_count,
            "has_more": True,
        },
    }

    # tree
    treeRoot = Taxon.objects.filter(rank="kingdom").all()
    treeData = [
        {
            "id": x.id,
            "data": {
                "name": x.get_name(),
                "count": x.count,
            },
        }
        for x in treeRoot
    ]
    ret["tree"] = treeData
    return JsonResponse(ret)


# ------- DEPRECATED ------#


def export(request):
    solr = SolrQuery("taibif_occurrence")
    solr_url = solr.generate_export_solr_url(request.GET)
    generateCSV(solr_url, request)

    return JsonResponse({"status": "success"}, safe=False)


@shared_task
def generateCSV(solr_url, request):
    CSV_MEDIA_FOLDER = "csv"
    csvFolder = os.path.join(conf_settings.MEDIA_ROOT, CSV_MEDIA_FOLDER)
    timestramp = str(int(time.time()))
    type = request.GET["type"]
    tempFilename = f"{timestramp}_temp.csv"
    filename = f"{type}_{timestramp}.csv"
    downloadURL = "没有任何資料"
    csvFileTempPath = os.path.join(csvFolder, tempFilename)
    csvFilePath = os.path.join(csvFolder, filename)
    dataPolicyURL = "https://" + request.META["HTTP_HOST"] + "/data-policy"
    if not os.path.exists(csvFolder):
        os.makedirs(csvFolder)

    logger.info(f"REQUEST QUERYSET: {request}")

    # if solr_url:
    #     downloadURL = f"https://{request.META['HTTP_HOST']}{conf_settings.MEDIA_URL}{os.path.join(CSV_MEDIA_FOLDER, filename)}"
    #     if type == 'species' :
    #         command = 'curl "'+solr_url+'" >  '+csvFileTempPath+'  &&  ( head -1 '+csvFileTempPath+' && tail -n+2 '+csvFileTempPath+'  | awk \'BEGIN{FS=OFS=","}NF=(NF-1)\'  | awk -F , \'{a[$0]++; next}END {for (i in a) print i", "a[i]}\'| awk -F , \'!seen[$1]++\' ) > '+csvFilePath+' && rm -rf '+csvFileTempPath
    #     else:
    #         command = f'curl "{solr_url}" > "{csvFilePath}"'

    #     try:
    #         result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         logger.info('CURL SUCCESSFULLY OPERATED')
    #     except subprocess.CalledProcessError as e:
    #         logger.error(f'CURL COMMAND FAILED WITH ERROR: {e.stderr.decode("utf-8")}')
    #         raise

    if solr_url:
        downloadURL = f"https://{request.META['HTTP_HOST']}{conf_settings.MEDIA_URL}{os.path.join(CSV_MEDIA_FOLDER, filename)}"
        if type == "species":
            command = 'curl "' + solr_url + '" > ' + csvFileTempPath
            try:
                subprocess.run(command, shell=True, check=True)
                logger.info("Curl CSV file successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f'Failed to curl CSV file: {e.stderr.decode("utf-8")}')
                raise

            with open(csvFileTempPath, "r", encoding="utf-8") as temp_file, open(
                csvFilePath, "w", newline="", encoding="utf-8"
            ) as final_file:
                reader = csv.DictReader(temp_file)
                # 選擇 species list 要保留的欄位
                fields_to_keep = [
                    "taibif_taicolTaxonID",
                    "taibif_scientificName",
                    "taibif_kingdom",
                    "taibif_phylum",
                    "taibif_class",
                    "taibif_order",
                    "taibif_family",
                    "taibif_genus",
                    "taibif_taxonRank",
                    "taibif_taxonBackbone",
                ]
                writer = csv.DictWriter(final_file, fieldnames=fields_to_keep)
                writer.writeheader()

                # 追蹤已經寫入 final_file 的 row，避免重複
                seen_rows = set()

                # 逐 row 處理 temp_file 的內容，剔除重複的 row
                for row in reader:
                    filtered_row = {key: row[key] for key in fields_to_keep}
                    row_tuple = tuple(filtered_row.values())

                    if row_tuple not in seen_rows:
                        writer.writerow(filtered_row)
                        seen_rows.add(row_tuple)

            # 刪除過渡檔案 temp_file
            os.remove(csvFileTempPath)
            logger.info("Processed CSV file and removed duplicates")
        else:
            # 直接下载到指定的 CSV 文件
            command = f'curl "{solr_url}" > "{csvFilePath}"'
            try:
                subprocess.run(command, shell=True, check=True)
                logger.info("Curl CSV file successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f'Failed to curl CSV file: {e.stderr.decode("utf-8")}')
                raise

        sendMail(downloadURL, request, dataPolicyURL)


def sendMail(downloadURL, request, dataPolicyURL):
    license = "CC-BY-NC 4.0"
    datasets = request.GET.getlist("dataset")
    facet_dataset = "dataset:{type:terms,field:taibif_dataset_name_zh}"
    facet_license = "dataset:{type:terms,field:license}"
    facet_json = "json.facet={" + facet_dataset + "," + facet_license + "}"

    for dataset in datasets:
        r = requests.get(
            f"http://solr:8983/solr/taibif_occurrence/select?fl=license&fq=taibif_dataset_name:({quote(dataset)})&q.op=OR&q=*%3A*&rows=1"
        )

        if r.status_code == 200:
            data = r.json()
            print(data)
            search_count = data["response"]["numFound"]
            if search_count != 0:
                datasetLicense = data["response"]["docs"][0]["license"]
                if datasetLicense == "CC-BY-NC 4.0":
                    license = datasetLicense
                else:
                    license = "未明確授權"

    subject = "出現紀錄搜尋"

    currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    searchCondition = request.GET["search_condition"]

    html = f"""\
<html>
  <head></head>
  <body style='text-align:left'>
您好，
<br/><br/>
您在TaiBIF上查詢的檔案已夾帶於附件中，

<br/><br/>
檔案相關的詳細說明為：

<br/><br/>
搜尋條件：{searchCondition}


<br/>
搜尋時間：{currentTime}

<br/><br/>
檔案類型：CSV

<br/><br/>

授權條款： {license}

<br/><br/>

使用條款：<a href="{dataPolicyURL}">{dataPolicyURL}</a>

<br/><br/>
下載連結：<a href="{downloadURL}">{downloadURL}</a>

<br/><br/>
若有問題再麻煩您回覆至

<br/><br/>
<a href='mailto:taibif.brcas@gmail.com'>taibif.brcas@gmail.com</a>

<br/><br/>
TaiBIF團隊 敬上
  </body>
</html>
"""

    send_mail(
        subject,
        None,
        conf_settings.TAIBIF_SERVICE_EMAIL,
        [request.GET["email"]],
        html_message=html,
    )


def get_autocomplete_taxon(request):
    names = []
    if keyword_str := request.GET.get("keyword", "").strip():
        regex_string = "^" + keyword_str + ".*"
        autocomplete_taxon = Taxon.objects.filter(name__iregex=regex_string)[:10]

        if autocomplete_taxon:
            names = [
                {
                    "key": x.taicol_taxon_id,
                    "name": x.name,
                    "label": x.name,
                }
                for x in autocomplete_taxon
            ]

    return HttpResponse(json.dumps(names), content_type="application/json")


def get_map_geojson(request):
    solr_url = request.GET.get("solr_url")
    if not solr_url:
        return JsonResponse({"error": "solr_url parameter is required"}, status=400)

    geojson_data = get_geojson(solr_url)
    return JsonResponse(geojson_data)


from collections import defaultdict


def get_heatmap_data(request):
    x_axis = request.GET.get("xAxis")
    y_axis = request.GET.get("yAxis")
    pivot_key = f"{x_axis},{y_axis}"
    # print(f'x_axis: {x_axis}, y_axis: {y_axis}')
    url = "http://solr:8983/solr/taibif_occurrence/select"
    params = {
        "indent": "true",
        "q": "basisOfRecord:*",
        "facet": "true",
        "facet.pivot": pivot_key,
        "rows": 0,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to fetch data from Solr"}, status=response.status_code
        )
    data = response.json()
    pivot_results = data.get("facet_counts", {}).get("facet_pivot", {})

    # 分組和統計
    heatmap_data = defaultdict(lambda: defaultdict(int))
    has_more_results = True

    if y_axis == "taibif_country":
        # 先取得所有 taibif_country 的列表
        url = "http://solr:8983/solr/taibif_occurrence/select"
        params = {
            "q": "basisOfRecord:*",
            "rows": 0,
            "indent": "true",
            "facet": "true",
            "facet.field": "taibif_country",
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            return JsonResponse(
                {"error": "Failed to fetch data from Solr"}, status=response.status_code
            )

        solr_results = response.json()
        # print(f'SOLR RESULTS: {solr_results}')
        facet_counts = solr_results.get("facet_counts", {})
        facet_data = facet_counts.get("facet_fields", {}).get("taibif_country", [])
        country_list = [facet_data[i] for i in range(0, len(facet_data), 2)]

        pagination_number = int(request.GET.get("countryPagination", 0))
        range_start = 10 * pagination_number
        range_end = min(10 * (pagination_number + 1), len(country_list))
        # 用國家名稱實現分頁功能
        paginated_countries = country_list[range_start:range_end]

        has_more_results = range_end < len(country_list)

        for bucket in pivot_results[pivot_key]:
            variable = bucket["value"]
            print(f"bucket: {bucket}")
            if "pivot" in bucket:  # 處理缺少 pivot 字段的問題
                for pivot in bucket["pivot"]:
                    group = pivot["value"]
                    count = pivot["count"]
                    if group in paginated_countries:  # 控制傳遞回前端的內容
                        heatmap_data[group][variable] = count
    elif x_axis == "taibif_country":
        pagination_number = int(request.GET.get("countryPagination", 0))
        range_start = 10 * pagination_number
        range_end = min(10 * (pagination_number + 1), len(pivot_results[pivot_key]))

        has_more_results = range_end < len(pivot_results[pivot_key])

        paginated_buckets = pivot_results[pivot_key][range_start:range_end]

        for bucket in paginated_buckets:
            variable = bucket["value"]
            for pivot in bucket["pivot"]:
                group = pivot["value"]
                count = pivot["count"]
                heatmap_data[group][variable] = count
    else:
        for bucket in pivot_results[pivot_key]:
            variable = bucket["value"]
            for pivot in bucket["pivot"]:
                group = pivot["value"]
                count = pivot["count"]
                heatmap_data[group][variable] = count
    # print(f'HEATMAP DATA: {heatmap_data}')

    # 將結果轉換為繪製 heatmap 所需的格式
    formatted_heatmap_data = []
    for variable, group_counts in heatmap_data.items():
        for group, count in group_counts.items():
            formatted_heatmap_data.append(
                {"variable": variable, "group": group, "count": count}
            )

    # print(f'HEATMAP RESULTS: {formatted_heatmap_data}')

    return JsonResponse(
        {"data": formatted_heatmap_data, "has_more_results": has_more_results}
    )


def get_barchart_data(request):
    facet_field = request.GET.get("yAxis")
    if not facet_field:
        return JsonResponse({"error": "facetField parameter is required"}, status=400)
    url = "http://solr:8983/solr/taibif_occurrence/select"
    params = {
        "q": "basisOfRecord:*",
        "rows": 0,
        "indent": "true",
        "facet": "true",
        "facet.field": facet_field,
    }

    # 初始化所有回傳參數
    bar_chart_data = []
    has_more_results = False

    # 如果 facet_field 是 taibif_year，添加年份範圍過濾器
    if facet_field == "taibif_year":
        start_year = request.GET.get("startYear")
        end_year = request.GET.get("endYear")
        # print(f'START YEAR: {start_year}, END YEAR: {end_year}')

        if not start_year or not end_year:
            return JsonResponse(
                {
                    "error": "start_year and end_year parameters are required for taibif_year"
                },
                status=400,
            )

        # 添加範圍過濾器
        params["fq"] = f"{facet_field}:[{start_year} TO {end_year}]"

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to fetch data from Solr"}, status=response.status_code
        )

    solr_results = response.json()
    # print(f'SOLR RESULTS: {solr_results}')
    facet_counts = solr_results.get("facet_counts", {})
    facet_data = facet_counts.get("facet_fields", {}).get(facet_field, [])

    if facet_field == "taibif_country":
        pagination_number = int(request.GET.get("countryPagination", 0))
        range_start = 20 * pagination_number
        range_end = min(20 * (pagination_number + 1), len(facet_data))

        if range_start >= len(facet_data):
            has_more_results = False
        else:
            bar_chart_data = [
                {"name": facet_data[i], "value": facet_data[i + 1]}
                for i in range(range_start, range_end, 2)
                if i + 1 < len(facet_data)
            ]
            has_more_results = range_end < len(facet_data)
    else:
        bar_chart_data = [
            {"name": facet_data[i], "value": facet_data[i + 1]}
            for i in range(0, len(facet_data), 2)
        ]

    return JsonResponse(
        {"chart_data": bar_chart_data, "has_more_results": has_more_results}
    )


def solr_pivot_to_d3_hierarchy(pivot_data, field_name="Root", color="#D3D3D3"):
    """
    將 Solr 的 facet_pivot 數據轉換為 D3 嵌套結構。
    :param pivot_data: Solr 的 facet_pivot 數據（列表格式）
    :param field_name: 當前層的名稱（默認為 "Root"）
    :return: D3 的層次結構格式數據
    """
    kingdom_color_map = {
        "Animalia": "#6C5B7B",  # 深紫灰
        "Archaea": "#C06C84",  # 暗玫瑰紅
        "Bacteria": "#F8B195",  # 柔暖杏色
        "Chromista": "#355C7D",  # 深灰藍
        "Fungi": "#A8B8A5",  # 橄欖灰綠
        "Plantae": "#F67280",  # 莓果粉紅
        "Protozoa": "#99B898",  # 柔嫩青綠
        "Viruses": "#3E454C",  # 深煙灰
    }

    hierarchy = {"name": field_name, "children": [], "color": "#D3D3D3"}

    for item in pivot_data:
        kingdom_color = kingdom_color_map.get(item["value"], None)

        if kingdom_color is not None:
            color = kingdom_color
        # 創建當前節點
        node = {"name": item["value"], "value": item["count"], "color": color}

        # 如果有子節點，遞歸處理
        if "pivot" in item:
            node["children"] = solr_pivot_to_d3_hierarchy(
                item["pivot"], item["field"], color
            )["children"]
        else:
            node["children"] = []

        hierarchy["children"].append(node)

    return hierarchy


def get_dataset_sunburst_data(request):
    taibif_dataset_id = "8a6e2a2e-85f9-44ce-a3c5-b0b10266a0ed"
    solr_pivot_fields = "&facet.pivot=taibif_kingdom,taibif_phylum,taibif_class,taibif_order,taibif_family,taibif_genus"
    url = f"http://solr:8983/solr/taibif_occurrence/select?{solr_pivot_fields}&facet.mincount=1&facet=true&fq=taibif_datasetKey:{taibif_dataset_id}&indent=true&q.op=OR&q=*%3A*&rows=0"
    solr_response = requests.get(url).json()
    pivot_results = (
        solr_response.get("facet_counts")
        .get("facet_pivot")
        .get(
            "taibif_kingdom,taibif_phylum,taibif_class,taibif_order,taibif_family,taibif_genus"
        )
    )
    d3_data = solr_pivot_to_d3_hierarchy(pivot_results)

    return JsonResponse(d3_data)


def fetch_facet_data(solr_url, facet_field):
    """向 solr 發送請求並解析 facet 結果"""
    try:
        response = requests.get(solr_url).json()
        facet_results = (
            response.get("facet_counts", {})
            .get("facet_fields", {})
            .get(facet_field, [])
        )
        if facet_results:
            return dict(zip(facet_results[::2], facet_results[1::2]))
        return {}
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch data from Solr: {e}")


def get_dataset_taxon_tree_data(request):
    taibif_dataset_id = request.GET.get("dataset_id")
    parent_rank = request.GET.get("parent_rank")
    parent_name = request.GET.get("parent_name")

    rank_hierarchy = [
        "taibif_kingdom",
        "taibif_phylum",
        "taibif_class",
        "taibif_order",
        "taibif_family",
        "taibif_genus",
        "taibif_scientificName",
    ]

    # 確定子層級
    if parent_rank and parent_rank in rank_hierarchy:
        parent_index = rank_hierarchy.index(parent_rank)
        if parent_index + 1 < len(rank_hierarchy):
            child_rank = rank_hierarchy[parent_index + 1]
        else:
            return JsonResponse({"node": []})  # 已是最底層
    else:
        child_rank = rank_hierarchy[0]  # 默認為最高層級

    solr_facet_fields = f"facet.field={child_rank}"
    filter_query = f"fq=taibif_datasetKey:{taibif_dataset_id}"
    if parent_rank and parent_name:
        filter_query += f"&fq={parent_rank}:{parent_name}"

    solr_url = (
        f"http://solr:8983/solr/taibif_occurrence/select?"
        f"{solr_facet_fields}&facet.mincount=1&facet=true&{filter_query}"
        f"&indent=true&q.op=OR&q=*:*&rows=0"
    )

    nodes = []
    try:
        facet_data = fetch_facet_data(solr_url, child_rank)
        for name, count in facet_data.items():
            taxon_data = (
                Taxon.objects.filter(name=name)
                .values("name_zh", "taicol_taxon_id")
                .first()
            )
            if taxon_data:
                nodes.append(
                    {
                        "scientific_name": name,
                        "count": count,
                        "rank": child_rank,
                        "name_zh": taxon_data.get("name_zh"),
                        "taicol_taxon_id": taxon_data.get("taicol_taxon_id"),
                    }
                )
            else:
                nodes.append(
                    {
                        "scientific_name": name,
                        "count": count,
                        "rank": child_rank,
                        "name_zh": None,
                        "taicol_taxon_id": None,
                    }
                )
        # nodes = [
        #     {'scientific_name': name, 'count': count, 'rank': child_rank}
        #     for name, count in facet_data.items()
        # ]

        response_data = (
            {"root": nodes} if child_rank == rank_hierarchy[0] else {"node": nodes}
        )
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def parse_datetime_data(list_object, data):
    if data is None:
        return list_object
    for label_str, count in data.items():
        if int(label_str) > 0:
            list_object.append({"label": int(label_str), "count": count})
    list_object = sorted(list_object, key=lambda x: x["label"])

    return list_object


def get_dataset_datetime_data(request):
    taibif_dataset_id = request.GET.get("dataset_id")
    facet_field_list = ["taibif_year", "taibif_month"]
    year_data_list = []
    month_data_list = []

    solr_facet_fields = "&".join([f"facet.field={field}" for field in facet_field_list])
    filter_query = f"fq=taibif_datasetKey:{taibif_dataset_id}"

    solr_url = (
        f"http://solr:8983/solr/taibif_occurrence/select?"
        f"{solr_facet_fields}&facet.mincount=1&facet=true&{filter_query}"
        f"&indent=true&q.op=OR&q=*:*&rows=0"
    )

    try:
        facet_data_year = fetch_facet_data(solr_url, "taibif_year")
        facet_data_month = fetch_facet_data(solr_url, "taibif_month")

        year_data_list = parse_datetime_data(year_data_list, facet_data_year)
        month_data_list = parse_datetime_data(month_data_list, facet_data_month)

        respoonse_data = {"year": year_data_list, "month": month_data_list}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(respoonse_data)


def occurrence_search_gallery(request):
    query_params = request.GET
    solr = SolrQuery("taibif_occurrence")

    if len(query_params) > 0:
        solr_url = solr.generate_gallery_solr_url(query_params)
    else:
        solr_url = solr.generate_gallery_solr_url()

    try:
        response = requests.get(solr_url)
        response.raise_for_status()
        solr_data = response.json().get("response", {}).get("docs", [])
        current_cursor = (
            response.json()
            .get("responseHeader", {})
            .get("params", {})
            .get("cursorMark")
        )
        next_cursor = response.json().get("nextCursorMark")
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Solr request failed: {str(e)}"}, status=500)

    expanded_solr_data = []
    for data in solr_data:
        if "taibif_mediaReferences" in data and data["taibif_mediaReferences"]:
            mediaList = data["taibif_mediaReferences"].split("|")
            for media in mediaList:
                expanded_solr_data.append(
                    {
                        "taibif_scientificName": data.get("taibif_scientificName", ""),
                        "taibif_mediaReferences": media,
                        "taibif_occurrence_id": data.get("taibif_occ_id", ""),
                    }
                )

    response = {
        "url": solr_url,
        "current_cursor": current_cursor,
        "next_cursor": next_cursor,
        "data": expanded_solr_data,
    }
    return JsonResponse(response, safe=False)
