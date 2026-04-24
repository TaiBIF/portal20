import datetime
import csv
import requests
import os
import re
import ast
from functools import lru_cache
from html import unescape

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models import Q
from django.http import (
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
from django.urls import reverse
from django.conf import settings

from .models import (
    Taxon,
    Occurrence,
    Dataset,
    Dataset_citation,
    Dataset_keyword,
    Dataset_Contact,
    Dataset_description,
    DatasetOrganization,
)
from .helpers.species import get_species_info
from .helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
)
from apps.article.models import Article
from apps.data.helpers.synonyms_variants_convertion import *
from utils.solr_query import SolrQuery
from utils.map_data import get_geojson
from apps.data.models import DATA_MAPPING
from conf.settings import ENV

DWC_CORE_TYPE_MAP = {
    "MEATADATA": "詮釋資料",
    "CHECKLIST": "物種名錄",
    "OCCURRENCE": "出現紀錄",
    "SAMPLINGEVENT": "調查活動",
}

STATIC_PAGE_SEARCH_ITEMS = [
    {
        "url_name": "about-taibif",
        "title": "TaiBIF 介紹與成果",
        "template": "about-taibif.html",
    },
    {"url_name": "about-gbif", "title": "GBIF 介紹", "template": "about-gbif.html"},
    {"url_name": "open_data", "title": "開放資料", "template": "open-data.html"},
    {
        "url_name": "open-process",
        "title": "有哪些步驟",
        "template": "open-process.html",
    },
    {
        "url_name": "open-benefits",
        "title": "開放資料的好處",
        "template": "open-benefits.html",
    },
    {
        "url_name": "open-metadata",
        "title": "詮釋資料",
        "template": "open-metadata.html",
    },
    {"url_name": "open-license", "title": "資料授權", "template": "open-license.html"},
    {"url_name": "open-upload", "title": "資料上傳", "template": "open-upload.html"},
    {
        "url_name": "open-consulation",
        "title": "我需要幫忙",
        "template": "open-consulation.html",
    },
    {"url_name": "tools", "title": "有哪工具可以使用", "template": "tools.html"},
    {"url_name": "data-stats", "title": "資料發布狀況", "template": "data-stats.html"},
    {"url_name": "data-clean", "title": "清理資料", "template": "data-clean.html"},
    {"url_name": "data-case", "title": "給我一些例子", "template": "data-case.html"},
    {
        "url_name": "data-paper",
        "title": "資料期刊與論文",
        "template": "data-paper.html",
    },
    {
        "url_name": "data-product",
        "title": "有哪些資料產品",
        "template": "data-product.html",
    },
    {"url_name": "tech-book", "title": "什麼是開放資料", "template": "tech-book.html"},
    {
        "url_name": "tech-workshop",
        "title": "參加 TaiBIF 工作坊",
        "template": "tech-workshop.html",
    },
    {
        "url_name": "tech-volunteer",
        "title": "參與協作者培訓",
        "template": "tech-volunteer.html",
    },
    {
        "url_name": "tech-online-class",
        "title": "線上教材包",
        "template": "tech-online-class.html",
    },
    {"url_name": "faq", "title": "開放資料常見問題", "template": "faq.html"},
    {
        "url_name": "monthly-status",
        "title": "每月資料發佈狀況",
        "template": "monthly-status.html",
    },
    {
        "url_name": "thanks-list",
        "title": "感謝名單",
        "template": "thanks-list.html",
    },
    {
        "url_name": "taibif-api",
        "title": "TaiBIF API",
        "template": "taibif-api.html",
    },
    {
        "url_name": "data-policy",
        "title": "資料使用條款暨隱私權政策",
        "template": "data-policy.html",
    },
]

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)
_TRANS_TAG_RE = re.compile(
    r"{%\s*trans\s+((?:\"(?:\\.|[^\"])*\")|(?:'(?:\\.|[^'])*'))(?:\s+[^%]*)?%}",
    re.DOTALL,
)
_BLOCKTRANS_START_RE = re.compile(
    r"{%\s*(?:blocktrans|transblock)(?:\s+[^%]*)?%}",
    re.IGNORECASE,
)
_BLOCKTRANS_END_RE = re.compile(
    r"{%\s*(?:endblocktrans|endtransblock)\s*%}",
    re.IGNORECASE,
)
_DJANGO_TAG_RE = re.compile(r"({%.*?%}|{{.*?}}|{#.*?#})", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def _unquote_template_string(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("\"'")


def _preserve_translation_text(raw_html):
    text = _TRANS_TAG_RE.sub(lambda m: _unquote_template_string(m.group(1)), raw_html)
    text = _BLOCKTRANS_START_RE.sub(" ", text)
    text = _BLOCKTRANS_END_RE.sub(" ", text)
    return text


def _clean_template_text(raw_html):
    text = _SCRIPT_STYLE_RE.sub(" ", raw_html)
    text = _preserve_translation_text(text)
    text = _DJANGO_TAG_RE.sub(" ", text)
    text = _HTML_TAG_RE.sub(" ", text)
    text = unescape(text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


@lru_cache(maxsize=128)
def _load_template_visible_text(template_name):
    template_path = os.path.join(settings.BASE_DIR, "templates", template_name)
    if not os.path.exists(template_path):
        return ""
    with open(template_path, "r", encoding="utf-8") as f:
        raw = f.read()
    return _clean_template_text(raw)


def search_all(request):
    if request.method == "POST":
        q = request.POST.get("q", "")
        url = "/search/"
        if q:
            url = "{}?q={}".format(url, q)
        return HttpResponseRedirect(url)
    elif request.method == "GET":
        q = request.GET.get("q", "")
        selected_targets = request.GET.getlist("target")
        valid_targets = {"static", "dataset", "publisher", "article"}
        selected_targets = [x for x in selected_targets if x in valid_targets]
        if not selected_targets:
            selected_targets = ["static", "dataset", "publisher", "article"]
        mappings = load_mappings()
        variant_map = mappings["variant_map"]
        synonyms_map = mappings["synonyms_map"]

        # 同義字轉換
        q_synonyms = replace_synonyms(q, synonyms_map)
        # 生成所有可能的異體字組合
        query_variants = generate_variants(q_synonyms, variant_map)

        # dataset
        dataset_rows = []
        if "dataset" in selected_targets:
            query = Q()
            for variant in query_variants:
                query |= Q(title__icontains=variant) | Q(name__icontains=variant)
            for x in (
                Dataset.objects.values(
                    "title", "name", "id", "taibif_dataset_id", "dwc_core_type"
                )
                .filter(query)
                .exclude(status="PRIVATE")
                .all()[:5]
            ):
                tmp_content = Dataset_description.objects.filter(
                    dataset=x["id"]
                ).order_by("seq")
                if len(tmp_content) > 0:
                    tmp_content = (
                        Dataset_description.objects.filter(dataset=x["id"])
                        .order_by("seq")[0]
                        .description
                    )
                else:
                    tmp_content = ""
                dwc_core_type = DWC_CORE_TYPE_MAP.get(x["dwc_core_type"], "Unknown")
                dataset_rows.append(
                    {
                        "title": x["title"] if x["title"] != "" else x["name"],
                        "dwc_core_type": dwc_core_type,
                        "content": tmp_content,
                        "url": "/dataset/{}".format(x["taibif_dataset_id"]),
                    }
                )

        # publisher
        publisher_rows = []
        if "publisher" in selected_targets:
            query = Q()
            for variant in query_variants:
                query |= Q(name__icontains=variant)
            for x in DatasetOrganization.objects.filter(query).all()[:5]:
                publisher_rows.append(
                    {
                        "title": x.name,
                        "content": x.description,
                        "url": "/publisher/{}".format(x.id),
                    }
                )

        # article
        article_rows = []
        if "article" in selected_targets:
            query = Q()
            for variant in query_variants:
                query |= Q(title__icontains=variant) | Q(content__icontains=variant)
            for x in Article.objects.filter(query).all()[:5]:
                article_rows.append(
                    {
                        "title": x.title,
                        "content": x.content,
                        "url": reverse("article-detail-id", kwargs={"pk": x.id}),
                    }
                )

        # static pages
        static_rows = []
        if "static" in selected_targets:
            q_variants_lower = [x.lower() for x in query_variants if x]
            for page in STATIC_PAGE_SEARCH_ITEMS:
                visible_text = _load_template_visible_text(page["template"])
                target = f"{page['title']} {visible_text}".lower()
                matched_variant = next(
                    (v for v in q_variants_lower if v in target), None
                )
                if matched_variant:
                    static_rows.append(
                        {
                            "title": page["title"],
                            "content": visible_text,
                            "url": reverse(page["url_name"]),
                        }
                    )

        static_page_obj = None
        if "static" in selected_targets:
            static_paginator = Paginator(static_rows, 10)
            static_page_num = request.GET.get("page", 1)
            static_page_obj = static_paginator.get_page(static_page_num)
            static_rows = list(static_page_obj.object_list)
        else:
            static_rows = []

        results = []
        if "static" in selected_targets:
            results.append({"cat": "static", "label": "靜態頁面", "rows": static_rows})
        if "dataset" in selected_targets:
            results.append({"cat": "dataset", "label": "資料集", "rows": dataset_rows})
        if "publisher" in selected_targets:
            results.append(
                {"cat": "publisher", "label": "發布單位", "rows": publisher_rows}
            )
        if "article" in selected_targets:
            results.append({"cat": "article", "label": "最新消息", "rows": article_rows})

        context = {
            "results": results,
            "selected_targets": selected_targets,
            "has_results": any(result["rows"] for result in results),
            "static_page_obj": static_page_obj,
        }

        return render(request, "search_all.html", context)


def occurrence_view(request, taibif_id):

    solr = SolrQuery("taibif_occurrence", None, None)
    req = solr.get_occurrence(taibif_id)
    result = req["results"]

    intro = {}
    record = {}
    occ = {}
    event = {}
    taxon = {}
    location = {}
    other = {}

    lat = 0
    lon = 0
    # intro
    # TODO

    if result:
        intro["dataset_zh"] = (
            result[0].get("taibif_dataset_name_zh")
            if result[0].get("taibif_dataset_name_zh")
            else None
        )
        intro["taibif_datasetKey"] = (
            result[0].get("taibif_datasetKey")
            if result[0].get("taibif_datasetKey")
            else None
        )
        intro["publisher"] = (
            result[0].get("publisher") if result[0].get("publisher") else None
        )
        intro["basisOfRecord"] = (
            result[0].get("basisOfRecord") if result[0].get("basisOfRecord") else None
        )

        # Fix the error of Nonetype
        original_scientific_name = result[0].get("scientificName")
        if original_scientific_name:
            if "sp" in original_scientific_name:
                genus_name = original_scientific_name.split(" ")[0]
                sp = original_scientific_name.split(" ")[1]
                intro["scientificName"] = f"<em>{genus_name}</em>  {sp}"
            else:
                intro["scientificName"] = (
                    result[0].get("taibif_formattedName")
                    if result[0].get("taibif_formattedName")
                    else result[0].get("taibif_scientificName")
                )

        # intro['scientificName']=result[0].get('formatted_name') if result[0].get('formatted_name') else f"<em>{result[0].get('scientificName')}</em>"
        intro["scientificName_zh"] = (
            result[0].get("taibif_vernacularName")
            if result[0].get("taibif_vernacularName")
            else ""
        )

        intro["dataset"] = result[0].get("taibifDatasetID")
        issues = []
        if hasattr(result[0], "TaxonMatchNone") and result[0].get("TaxonMatchNone")[0]:
            issues.append("Taxon Match None")
        if (
            hasattr(result[0], "CoordinateInvalid")
            and result[0].get("CoordinateInvalid")[0]
        ):
            issues.append("Coordinate Invalid")
        if (
            hasattr(result[0], "RecordedDateInvalid")
            and result[0].get("RecordedDateInvalid")[0]
        ):
            issues.append("Recorded Date Invalid")
        intro["issues"] = issues

        # 多媒體資料
        intro["taibif_mediaReferences"] = (
            result[0].get("taibif_mediaReferences").split("|")
            if result[0].get("taibif_mediaReferences")
            else None
        )

        # record
        record["modified"] = {
            "name_zh": "資料更新時間",
            "value": [
                result[0].get("modified") if result[0].get("modified") else None,
                (
                    result[0].get("modified")
                    if result[0].get("modified")
                    else (
                        result[0].get("taibif_lastInterpreted")
                        if result[0].get("taibif_lastInterpreted")
                        else None
                    )
                ),
            ],
        }

        record["language"] = {
            "name_zh": "語言",
            "value": [result[0].get("language"), result[0].get("taibif_language")],
        }
        record["license"] = {
            "name_zh": "授權標示",
            "value": [result[0].get("taibif_license"), result[0].get("taibif_license")],
        }
        record["rightsHolder"] = {
            "name_zh": "所有權",
            "value": [
                result[0].get("rightsHolder"),
                result[0].get("taibif_rightsHolder"),
            ],
        }
        record["references"] = {
            "name_zh": "參考資料",
            "value": [result[0].get("references"), result[0].get("taibif_references")],
        }
        record["institutionID"] = {
            "name_zh": "機構ID",
            "value": [
                result[0].get("institutionID"),
                result[0].get("taibif_institutionID"),
            ],
        }
        record["collectionID"] = {
            "name_zh": "典藏ID",
            "value": [
                result[0].get("collectionID"),
                result[0].get("taibif_collectionID"),
            ],
        }
        record["datasetID"] = {
            "name_zh": "資料集ID",
            "value": [result[0].get("datasetID"), result[0].get("taibif_datasetID")],
        }
        record["institutionCode"] = {
            "name_zh": "機構代號",
            "value": [
                result[0].get("institutionCode"),
                result[0].get("taibif_institutionCode"),
            ],
        }
        record["collectionCode"] = {
            "name_zh": "典藏代號",
            "value": [
                result[0].get("collectionCode"),
                result[0].get("taibif_collectionCode"),
            ],
        }
        record["datasetName"] = {
            "name_zh": "資料集名稱",
            "value": [
                result[0].get("datasetName"),
                result[0].get("taibif_datasetName"),
            ],
        }
        record["ownerInstitutionCode"] = {
            "name_zh": "所有者機構代碼",
            "value": [
                result[0].get("ownerInstitutionCode"),
                result[0].get("taibif_ownerInstitutionCode"),
            ],
        }
        record["basisOfRecord"] = {
            "name_zh": "資料基底",
            "value": [
                result[0].get("asisOfRecord"),
                result[0].get("taibif_asisOfRecord"),
            ],
        }
        record["informationWithheld"] = {
            "name_zh": "其他隱藏資訊",
            "value": [
                result[0].get("informationWithheld"),
                result[0].get("taibif_informationWithheld"),
            ],
        }
        record["dataGeneralizations"] = {
            "name_zh": "資料模糊化",
            "value": [
                result[0].get("dataGeneralizations"),
                result[0].get("taibif_dataGeneralizations"),
            ],
        }

        # occ

        # 相關多媒體資訊
        raw_associated_media = result[0].get("mediaReferences")
        parsed_associated_media = (
            result[0].get("taibif_mediaReferences")
            if result[0].get("taibif_mediaReferences")
            else (
                result[0].get("mediaReferences")
                if result[0].get("mediaReferences")
                else None
            )
        )

        occ["catalogNumber"] = {
            "name_zh": "館藏號",
            "value": [
                result[0].get("catalogNumber"),
                result[0].get("taibif_catalogNumber"),
            ],
        }
        occ["occurrenceID"] = {
            "name_zh": "出現紀錄ID",
            "value": [
                result[0].get("occurrenceID"),
                result[0].get("taibif_occurrenceID"),
            ],
        }
        occ["recordNumber"] = {
            "name_zh": "採集號",
            "value": [
                result[0].get("recordNumber "),
                result[0].get("taibif_recordNumber "),
            ],
        }
        occ["recordedByID"] = {
            "name_zh": "記錄者ID",
            "value": [
                result[0].get("recordedByID"),
                result[0].get("taibif_recordedByID"),
            ],
        }
        occ["recordedBy"] = {
            "name_zh": "記錄者",
            "value": [result[0].get("recordedBy"), result[0].get("taibif_recordedBy")],
        }
        occ["individualCount"] = {
            "name_zh": "個體數量",
            "value": [
                result[0].get("individualCount"),
                result[0].get("taibif_individualCount"),
            ],
        }
        occ["organismQuantity"] = {
            "name_zh": "數量",
            "value": [
                result[0].get("organismQuantity"),
                result[0].get("taibif_organismQuantity"),
            ],
        }
        occ["organismQuantityType"] = {
            "name_zh": "數量單位",
            "value": [
                result[0].get("organismQuantityType"),
                result[0].get("taibif_organismQuantityType"),
            ],
        }
        occ["lifeStage"] = {
            "name_zh": "生活史階段",
            "value": [result[0].get("lifeStage"), result[0].get("taibif_lifeStage")],
        }
        occ["sex"] = {
            "name_zh": "性別",
            "value": [result[0].get("sex"), result[0].get("taibif_sex")],
        }
        occ["reproductiveCondition"] = {
            "name_zh": "生殖狀態",
            "value": [
                result[0].get("reproductiveCondition"),
                result[0].get("taibif_reproductiveCondition"),
            ],
        }
        occ["establishmentMeans"] = {
            "name_zh": "原生/外來/入侵等定義",
            "value": [
                result[0].get("establishmentMeans"),
                result[0].get("taibif_establishmentMeans"),
            ],
        }
        occ["behavior"] = {
            "name_zh": "行為",
            "value": [result[0].get("behavior"), result[0].get("taibif_behavior")],
        }
        occ["georeferenceVerificationStatus"] = {
            "name_zh": "位置點位狀態",
            "value": [
                result[0].get("georeferenceVerificationStatus"),
                result[0].get("taibif_georeferenceVerificationStatus"),
            ],
        }
        occ["occurrenceStatus"] = {
            "name_zh": "出現狀態",
            "value": [
                result[0].get("occurrenceStatus"),
                result[0].get("taibif_occurrenceStatus"),
            ],
        }
        occ["preparations"] = {
            "name_zh": "樣本狀態",
            "value": [
                result[0].get("preparations"),
                result[0].get("taibif_preparations"),
            ],
        }
        occ["disposition"] = {
            "name_zh": "樣本處置",
            "value": [
                result[0].get("disposition"),
                result[0].get("taibif_disposition"),
            ],
        }
        occ["associatedMedia"] = {
            "name_zh": "相關多媒體資訊",
            "value": [raw_associated_media, parsed_associated_media],
        }
        occ["associatedReferences"] = {
            "name_zh": "相關參考資料",
            "value": [
                result[0].get("associatedReferences"),
                result[0].get("taibif_associatedReferences"),
            ],
        }
        occ["associatedSequences"] = {
            "name_zh": "相關基因序列",
            "value": [
                result[0].get("associatedSequences"),
                result[0].get("taibif_associatedSequences"),
            ],
        }
        occ["associatedLicense"] = {
            "name_zh": "相關多媒體授權標示",
            "value": [
                result[0].get("mediaLicense"),
                result[0].get("taibif_mediaLicense"),
            ],
        }
        occ["associatedTaxa"] = {
            "name_zh": "相關物種",
            "value": [
                result[0].get("associatedTaxa"),
                result[0].get("taibif_associatedTaxa"),
            ],
        }
        occ["otherCatalogNumbers"] = {
            "name_zh": "其他ID",
            "value": [
                result[0].get("otherCatalogNumbers"),
                result[0].get("taibif_otherCatalogNumbers"),
            ],
        }
        occ["occurrenceRemarks"] = {
            "name_zh": "出現紀錄註記",
            "value": [
                result[0].get("occurrenceRemarks"),
                result[0].get("taibif_occurrenceRemarks"),
            ],
        }
        occ["typeStatus"] = {
            "name_zh": "學名標本模式",
            "value": [
                result[0].get("typeStatus") if result[0].get("typeStatus") else None,
                (
                    result[0].get("taibif_typeStatus")
                    if result[0].get("taibif_typeStatus")
                    else None
                ),
            ],
        }

        # event
        event["eventID"] = {
            "name_zh": "調查活動ID",
            "value": [result[0].get("eventID"), result[0].get("taibif_eventID")],
        }
        event["parentEventID"] = {
            "name_zh": "parentEventID",
            "value": [
                result[0].get("parentEventID"),
                result[0].get(" taibif_parentEventID"),
            ],
        }
        event["fieldNumber"] = {
            "name_zh": "野外調查編號",
            "value": [
                result[0].get("fieldNumber"),
                result[0].get("taibif_fieldNumber"),
            ],
        }
        event["eventDate"] = {
            "name_zh": "調查活動日期",
            "value": [result[0].get("eventDate"), result[0].get("taibif_eventDate")],
        }
        event["eventTime"] = {
            "name_zh": "調查活動時間",
            "value": [result[0].get("eventTime"), result[0].get("taibif_eventTime")],
        }
        event["startDayOfYear"] = {
            "name_zh": "起始年份",
            "value": [
                result[0].get("startDayOfYear"),
                result[0].get("staibif_startDayOfYear"),
            ],
        }
        event["endDayOfYear"] = {
            "name_zh": "結束年份",
            "value": [
                result[0].get("endDayOfYear"),
                result[0].get("taibif_endDayOfYear"),
            ],
        }

        tmp_y = None
        tmp_m = None
        tmp_d = None
        if result[0].get("taibif_year"):
            tmp_y = result[0].get("taibif_year")[0]
        if result[0].get("taibif_month"):
            tmp_m = result[0].get("taibif_month")[0]
        if result[0].get("taibif_day"):
            tmp_d = result[0].get("taibif_day")[0]
        event["year"] = {"name_zh": "年", "value": [result[0].get("year"), tmp_y]}
        event["month"] = {"name_zh": "月", "value": [result[0].get("month"), tmp_m]}
        event["day"] = {"name_zh": "日", "value": [result[0].get("day"), tmp_d]}

        event["verbatimEventDate"] = {
            "name_zh": "字面上調查活動日期",
            "value": [
                result[0].get("verbatimEventDate"),
                result[0].get("taibif_verbatimEventDate"),
            ],
        }
        event["habitat"] = {
            "name_zh": "棲地",
            "value": [result[0].get("habitat"), result[0].get("taibif_habitat")],
        }
        event["samplingProtocol"] = {
            "name_zh": "調查方法",
            "value": [
                result[0].get("samplingProtocol"),
                result[0].get("taibif_samplingProtocol"),
            ],
        }
        event["samplingEffort"] = {
            "name_zh": "調查努力量",
            "value": [
                result[0].get("samplingEffort"),
                result[0].get("taibif_samplingEffort"),
            ],
        }
        event["fieldNotes"] = {
            "name_zh": "野外調查註記",
            "value": [result[0].get("fieldNotes"), result[0].get("taibif_fieldNotes")],
        }
        event["eventRemarks"] = {
            "name_zh": "調查活動註記",
            "value": [
                result[0].get("eventRemarks"),
                result[0].get("taibif_eventRemarks"),
            ],
        }

        # taxon
        try:
            acceptedNameUsageID = int(float(result[0].get("acceptedNameUsageID")))
        except:
            acceptedNameUsageID = result[0].get("acceptedNameUsageID")

        taxon_obj_name = None
        taxon_obj_accepted_name = None
        if result[0].get("taxon_backbone") == "TaiCOL":
            if result[0].get("taibif_namecode"):
                taxon_obj_name = Taxon.objects.get(
                    taicol_taxon_id=result[0].get("taibif_namecode")
                )
            if result[0].get("taibif_accepted_namecode"):
                taxon_obj_accepted_name = Taxon.objects.get(
                    taicol_taxon_id=result[0].get("taibif_accepted_namecode")
                )

        taxon["taxonID"] = {
            "name_zh": "分類編碼",
            "value": [
                (
                    result[0].get("taxonID")
                    if result[0].get("taxonID")
                    else result[0].get("taxonKey")
                ),
                (
                    result[0].get("taxonID")
                    if result[0].get("taibifID")
                    else result[0].get("taibif_Key")
                ),
            ],
        }
        taxon["scientificNameID"] = {
            "name_zh": "學名編碼",
            "value": [
                result[0].get("scientificNameID"),
                taxon_obj_name.taicol_name_id if taxon_obj_name != None else None,
            ],
        }
        taxon["acceptedNameUsageID"] = {
            "name_zh": "有效學名編碼",
            "value": [
                acceptedNameUsageID,
                (
                    taxon_obj_accepted_name.taicol_name_id
                    if taxon_obj_accepted_name != None
                    else result[0].get("taibif_Key")
                ),
            ],
        }
        taxon["scientificNameTaxonID"] = {
            "name_zh": "Taicol物種編碼",
            "value": [
                "",
                (
                    result[0].get("taicol_taxon_id")[0]
                    if result[0].get("taicol_taxon_id")
                    else result[0].get("taibif_taicolTaxonID")
                ),
            ],
        }
        taxon["scientificName"] = {
            "name_zh": "學名",
            "value": [
                result[0].get("scientificName"),
                (
                    taxon_obj_name.name
                    if taxon_obj_name != None
                    else (
                        result[0].get("taibif_scientificName")
                        if result[0].get("taibif_scientificName")
                        else None
                    )
                ),
            ],
        }
        taxon["acceptedNameUsage"] = {
            "name_zh": "有效學名",
            "value": [
                result[0].get("acceptedNameUsage"),
                (
                    taxon_obj_accepted_name.name
                    if taxon_obj_accepted_name != None
                    else None
                ),
            ],
        }
        taxon["originalNameUsage"] = {
            "name_zh": "originalNameUsage",
            "value": [
                result[0].get("originalNameUsage"),
                result[0].get("taibif_originalNameUsage"),
            ],
        }
        taxon["nameAccordingTo"] = {
            "name_zh": "nameAccordingTo",
            "value": [
                result[0].get("nameAccordingTo"),
                result[0].get("taibif_nameAccordingTo"),
            ],
        }
        taxon["namePublishedIn"] = {
            "name_zh": "namePublishedIn",
            "value": [
                result[0].get("namePublishedIn"),
                result[0].get("taibif_namePublishedIn"),
            ],
        }
        taxon["higherClassification"] = {
            "name_zh": "高階分類階層",
            "value": [
                result[0].get("higherClassification"),
                result[0].get("taibif_higherClassification"),
            ],
        }
        taxon["kingdom"] = {
            "name_zh": "界",
            "value": [
                result[0].get("kingdom"),
                (
                    result[0].get("taibif_kingdom")
                    if result[0].get("taibif_kingdom")
                    else None
                ),
            ],
        }
        taxon["taxon_backbone"] = result[0].get("taxon_backbone")
        taxon["phylum"] = {
            "name_zh": "門",
            "value": [
                result[0].get("phylum"),
                (
                    result[0].get("taibif_phylum")
                    if result[0].get("taibif_phylum")
                    else None
                ),
            ],
        }
        taxon["class"] = {
            "name_zh": "綱",
            "value": [
                result[0].get("class"),
                (
                    result[0].get("taibif_class")
                    if result[0].get("taibif_class")
                    else None
                ),
            ],
        }
        taxon["order"] = {
            "name_zh": "目",
            "value": [
                result[0].get("order"),
                (
                    result[0].get("taibif_order")
                    if result[0].get("taibif_order")
                    else None
                ),
            ],
        }
        taxon["family"] = {
            "name_zh": "科",
            "value": [
                result[0].get("family"),
                (
                    result[0].get("taibif_family")
                    if result[0].get("taibif_family")
                    else None
                ),
            ],
        }
        taxon["genus"] = {
            "name_zh": "屬",
            "value": [
                result[0].get("genus"),
                (
                    result[0].get("taibif_genus")
                    if result[0].get("taibif_genus")
                    else None
                ),
            ],
        }
        taxon["subgenus"] = {
            "name_zh": "亞屬",
            "value": [result[0].get("subgenus"), result[0].get("taibif_subgenus")],
        }
        taxon["specificEpithet"] = {
            "name_zh": "種小名",
            "value": [
                result[0].get("specificEpithet"),
                result[0].get("taibif_specificEpithet"),
            ],
        }
        taxon["infraspecificEpithet"] = {
            "name_zh": "種以下別名",
            "value": [
                result[0].get("infraspecificEpithet"),
                result[0].get("taibif_infraspecificEpithet"),
            ],
        }
        taxon["taxonRank"] = {
            "name_zh": "分類位階",
            "value": [result[0].get("taxonRank"), result[0].get("taibif_taxonRank")],
        }
        taxon["verbatimTaxonRank"] = {
            "name_zh": "字面上分類位階",
            "value": [
                result[0].get("verbatimTaxonRank"),
                result[0].get("taibif_verbatimTaxonRank"),
            ],
        }
        taxon["scientificNameAuthorship"] = {
            "name_zh": "學名命名者",
            "value": [
                result[0].get("scientificNameAuthorship"),
                result[0].get("taibif_scientificNameAuthorship"),
            ],
        }
        taxon["vernacularName"] = {
            "name_zh": "俗名",
            "value": [
                result[0].get("vernacularName"),
                (
                    result[0].get("taibif_vernacularName")
                    if result[0].get("taibif_vernacularName") != None
                    else ""
                ),
            ],
        }
        taxon["nomenclaturalCode"] = {
            "name_zh": "nomenclaturalCode",
            "value": [
                result[0].get("nomenclaturalCode"),
                result[0].get("taibif_nomenclaturalCode"),
            ],
        }
        taxon["taxonRemarks"] = {
            "name_zh": "分類註記",
            "value": [
                result[0].get("taxonRemarks"),
                result[0].get("taibif_taxonRemarks"),
            ],
        }

        lat = None
        lon = None
        lat_d = None
        lon_d = None
        if result[0].get("taibif_decimalLatitude"):
            lat = result[0].get("taibif_decimalLatitude")
            lat_d = result[0].get("taibif_decimalLatitude")
        elif result[0].get("decimalLatitude"):
            lat = result[0].get("decimalLatitude")

        if result[0].get("taibif_decimalLongitude"):
            lon = result[0].get("taibif_decimalLongitude")
            lon_d = result[0].get("taibif_decimalLongitude")
        elif result[0].get("decimalLongitude"):
            lon = result[0].get("decimalLongitude")

        # location
        location["locationID"] = {
            "name_zh": "地點ID",
            "value": [result[0].get("locationID"), result[0].get("taibif_locationID")],
        }
        location["higherGeographyID"] = {
            "name_zh": "higherGeographyID",
            "value": [
                result[0].get("higherGeographyID"),
                result[0].get("taibif_higherGeographyID"),
            ],
        }
        location["higherGeography"] = {
            "name_zh": "higherGeography",
            "value": [
                result[0].get("higherGeography"),
                result[0].get("taibif_higherGeography"),
            ],
        }
        location["continent"] = {
            "name_zh": "洲",
            "value": [result[0].get("continent"), result[0].get("taibif_continent")],
        }
        location["waterBody"] = {
            "name_zh": "水體",
            "value": [
                (
                    result[0].get("waterBody")[0]
                    if result[0].get("waterBody") != None
                    else result[0].get("waterBody")
                ),
                (
                    result[0].get("taibif_waterBody")[0]
                    if result[0].get("taibif_waterBody") != None
                    else result[0].get("taibif_waterBody")
                ),
            ],
        }
        location["islandGroup"] = {
            "name_zh": "群島",
            "value": [
                result[0].get("islandGroup"),
                result[0].get("taibif_islandGroup"),
            ],
        }
        location["island"] = {
            "name_zh": "島嶼",
            "value": [result[0].get("island"), result[0].get("taibif_island")],
        }
        location["country"] = {
            "name_zh": "國家",
            "value": [result[0].get("country"), result[0].get("taibif_country")],
        }
        location["countryCode"] = {
            "name_zh": "國家代碼",
            "value": [
                result[0].get("countryCode"),
                result[0].get("taibif_countryCode"),
            ],
        }
        location["stateProvince"] = {
            "name_zh": "省份/州",
            "value": [
                result[0].get("stateProvince"),
                result[0].get("taibif_stateProvince"),
            ],
        }
        location["county"] = {
            "name_zh": "縣市",
            "value": [
                result[0].get("county"),
                (
                    result[0].get("taibif_county_zh")
                    if result[0].get("taibif_county_zh")
                    else None
                ),
            ],
        }
        location["municipality"] = {
            "name_zh": "市",
            "value": [
                result[0].get("municipality"),
                result[0].get("taibif_municipality"),
            ],
        }
        location["locality"] = {
            "name_zh": "地區",
            "value": [result[0].get("locality"), result[0].get("taibif_locality")],
        }
        location["verbatimLocality"] = {
            "name_zh": "字面上地區",
            "value": [
                result[0].get("verbatimLocality"),
                result[0].get("taibif_verbatimLocality"),
            ],
        }
        location["minimumElevationInMeters"] = {
            "name_zh": "最低海拔(公尺)",
            "value": [
                result[0].get("minimumElevationInMeters"),
                result[0].get("taibif_minimumElevationInMeters"),
            ],
        }
        location["maximumElevationInMeters"] = {
            "name_zh": "最高海拔(公尺)",
            "value": [
                result[0].get("maximumElevationInMeters"),
                result[0].get("taibif_maximumElevationInMeters"),
            ],
        }
        location["verbatimElevation"] = {
            "name_zh": "字面上海拔",
            "value": [
                result[0].get("verbatimElevation"),
                result[0].get("verbatimElevation"),
            ],
        }
        location["minimumDepthInMeters"] = {
            "name_zh": "最小深度(公尺)",
            "value": [
                result[0].get("minimumDepthInMeters"),
                result[0].get("taibif_minimumDepthInMeters"),
            ],
        }
        location["maximumDepthInMeters"] = {
            "name_zh": "最大深度(公尺)",
            "value": [
                result[0].get("maximumDepthInMeters"),
                result[0].get("taibif_maximumDepthInMeters"),
            ],
        }
        location["verbatimDepth"] = {
            "name_zh": "字面上深度",
            "value": [
                result[0].get("verbatimDepth"),
                result[0].get("taibif_verbatimDepth"),
            ],
        }
        location["locationAccordingTo"] = {
            "name_zh": "locationAccordingTo",
            "value": [
                result[0].get("locationAccordingTo"),
                result[0].get("taibif_locationAccordingTo"),
            ],
        }
        location["locationRemarks"] = {
            "name_zh": "地點註記",
            "value": [
                result[0].get("locationRemarks"),
                result[0].get("taibif_locationRemarks"),
            ],
        }
        location["decimalLatitude"] = {
            "name_zh": "十進位緯度",
            "value": [result[0].get("decimalLatitude"), lat_d],
        }
        location["decimalLongitude"] = {
            "name_zh": "十進位經度",
            "value": [result[0].get("decimalLongitude"), lon_d],
        }
        location["geodeticDatum"] = {
            "name_zh": "大地測量基準",
            "value": [
                result[0].get("geodeticDatum"),
                result[0].get("taibif_geodeticDatum"),
            ],
        }
        location["coordinateUncertaintyInMeters"] = {
            "name_zh": "座標誤差(公尺)",
            "value": [
                (
                    result[0].get("coordinateUncertaintyInMeters")
                    if result[0].get("coordinateUncertaintyInMeters") != None
                    else None
                ),
                (
                    result[0].get("taibif_coordinateUncertaintyInMeters")[0]
                    if result[0].get("taibif_coordinateUncertaintyInMeters") != None
                    else None
                ),
            ],
        }
        location["coordinatePrecision"] = {
            "name_zh": "座標精準度",
            "value": [
                result[0].get("coordinatePrecision"),
                result[0].get("taibif_coordinatePrecision"),
            ],
        }
        location["pointRadiusSpatialFit"] = {
            "name_zh": "pointRadiusSpatialFit",
            "value": [
                result[0].get("pointRadiusSpatialFit"),
                result[0].get("taibif_pointRadiusSpatialFit"),
            ],
        }
        location["verbatimCoordinates"] = {
            "name_zh": "字面上座標",
            "value": [
                result[0].get("verbatimCoordinates"),
                result[0].get("verbatimCoordinates"),
            ],
        }
        location["verbatimLatitude"] = {
            "name_zh": "字面上緯度",
            "value": [
                result[0].get("verbatimLatitude"),
                result[0].get("verbatimLatitude"),
            ],
        }
        location["verbatimLongitude"] = {
            "name_zh": "字面上經度",
            "value": [
                result[0].get("verbatimLongitude"),
                result[0].get("verbatimLongitude"),
            ],
        }
        location["verbatimCoordinateSystem"] = {
            "name_zh": "字面上座標格式",
            "value": [
                result[0].get("verbatimCoordinateSystem"),
                result[0].get("verbatimCoordinateSystem"),
            ],
        }
        location["verbatimSRS"] = {
            "name_zh": "verbatimSRS",
            "value": [result[0].get("verbatimSRS"), result[0].get("verbatimSRS")],
        }
        location["footprintWKT"] = {
            "name_zh": "footprintWKT",
            "value": [result[0].get("footprintWKT"), result[0].get("footprintWKT")],
        }
        location["footprintSpatialFit"] = {
            "name_zh": "footprintSpatialFit",
            "value": [
                result[0].get("footprintSpatialFit"),
                result[0].get("taibif_footprintSpatialFit"),
            ],
        }
        location["georeferencedBy"] = {
            "name_zh": "地區紀錄者",
            "value": [
                result[0].get("georeferencedBy"),
                result[0].get("taibif_georeferencedBy"),
            ],
        }
        location["georeferencedDate"] = {
            "name_zh": "地區紀錄日期",
            "value": [
                result[0].get("georeferencedDate"),
                result[0].get("taibif_georeferencedDate"),
            ],
        }
        location["georeferenceProtocol"] = {
            "name_zh": "地區紀錄方法",
            "value": [
                result[0].get("georeferenceProtocol"),
                result[0].get("taibif_georeferenceProtocol"),
            ],
        }
        location["georeferenceSources"] = {
            "name_zh": "地區紀錄平台",
            "value": [
                result[0].get("georeferenceSources"),
                result[0].get("taibif_georeferenceSources"),
            ],
        }
        location["georeferenceRemarks"] = {
            "name_zh": "地區紀錄備註",
            "value": [
                result[0].get("georeferenceRemarks"),
                result[0].get("taibif_georeferenceRemarks"),
            ],
        }
    else:
        raise Http404("Occurrence does not exist")

    context = {
        "intro": intro,
        "record": record,
        "occ": occ,
        "event": event,
        "taxon": taxon,
        # 'taxon_error':taxon_error,
        "location": location,
        "other": other,
    }
    if lat and lon:
        context["map_view"] = [lat, lon]

    return render(request, "occurrence.html", context)


def dataset_view(request, taibif_dataset_id):

    try:
        dataset = (
            Dataset.objects.select_related("organization")
            .prefetch_related("dataset_description_set")
            .prefetch_related("dataset_contact_set")
            .prefetch_related("dataset_citation_set")
            .prefetch_related("dataset_keyword_set")
            .get(status="PUBLIC", taibif_dataset_id=taibif_dataset_id)
        )

        contacts = dataset.dataset_contact_set.all()
        citation = dataset.dataset_citation_set.all()
        description = dataset.dataset_description_set.first()
        keyword = dataset.dataset_keyword_set.all()

        solr_facet_fields = "facet.field=taibif_family&facet.field=taibif_genus&facet.field=grid_x&facet.field=grid_y&facet.field=taibif_year&facet.field=taibif_scientificName&facet.field=taxon_issue&facet.field=time_issue&facet.field=geo_issue"
        url = f"http://solr:8983/solr/taibif_occurrence/select?{solr_facet_fields}&facet.mincount=1&facet=true&fq=taibif_datasetKey:{taibif_dataset_id}&indent=true&q.op=OR&q=*%3A*&rows=0"
        solr_response = requests.get(url).json()
        facet_results = solr_response.get("facet_counts").get("facet_fields")
        record_counts = solr_response.get("response").get("numFound")

        family_facet_result = facet_results.get("taibif_family")
        taibif_counts = len(family_facet_result) // 2 if family_facet_result else 0

        genus_facet_result = facet_results.get("taibif_genus")
        genus_counts = len(genus_facet_result) // 2 if genus_facet_result else 0

        latitude_facet_result = facet_results.get("grid_x")
        latitude_counts = (
            sum(
                count
                for _, count in zip(
                    latitude_facet_result[::2], latitude_facet_result[1::2]
                )
            )
            if latitude_facet_result
            else 0
        )
        latitude_percent = (
            round((latitude_counts / record_counts) * 100, 1)
            if record_counts > 0
            else 0
        )

        longitude_facet_result = facet_results.get("grid_y")
        longitude_counts = (
            sum(
                count
                for _, count in zip(
                    longitude_facet_result[::2], longitude_facet_result[1::2]
                )
            )
            if longitude_facet_result
            else 0
        )
        longitude_percent = (
            round((longitude_counts / record_counts) * 100, 1)
            if record_counts > 0
            else 0
        )

        year_facet_result = facet_results.get("taibif_year")
        year_counts = (
            sum(
                count
                for _, count in zip(year_facet_result[::2], year_facet_result[1::2])
            )
            if year_facet_result
            else 0
        )
        year_percent = (
            round((year_counts / record_counts) * 100, 1) if record_counts > 0 else 0
        )

        taxon_facet_result = facet_results.get("taibif_scientificName")
        top_taxa = []
        if taxon_facet_result:
            taxa_dict = dict(zip(taxon_facet_result[::2], taxon_facet_result[1::2]))
            for name, count in list(taxa_dict.items())[:5]:
                taxon_data_from_db = (
                    Taxon.objects.filter(name=name)
                    .values("name_zh", "taicol_taxon_id")
                    .first()
                )
                if taxon_data_from_db:
                    top_taxa.append(
                        {
                            "scientific_name": name,
                            "count": count,
                            "name_zh": taxon_data_from_db.get("name_zh"),
                            "taicol_taxon_id": taxon_data_from_db.get(
                                "taicol_taxon_id"
                            ),
                        }
                    )
                else:
                    top_taxa.append(
                        {
                            "scientific_name": name,
                            "count": count,
                            "name_zh": None,
                            "taicol_taxon_id": None,
                        }
                    )
            # top_taxa = [{"scientific_name": name, "count": count} for name, count in list(taxa_dict.items())[:5]]

        taxon_issue_facet_result = facet_results.get("taxon_issue")
        taxon_issue = []
        if taxon_issue_facet_result:
            issue_dict = dict(
                zip(taxon_issue_facet_result[::2], taxon_issue_facet_result[1::2])
            )
            taxon_issue = [
                {"issue_type": name.upper(), "count": count}
                for name, count in list(issue_dict.items())
            ]

        time_issue_facet_result = facet_results.get("time_issue")
        time_issue = []
        if taxon_issue_facet_result:
            issue_dict = dict(
                zip(time_issue_facet_result[::2], time_issue_facet_result[1::2])
            )
            time_issue = [
                {"issue_type": name.upper(), "count": count}
                for name, count in list(issue_dict.items())
            ]

        geo_issue_facet_result = facet_results.get("geo_issue")
        geo_issue = []
        if geo_issue_facet_result:
            issue_dict = dict(
                zip(geo_issue_facet_result[::2], geo_issue_facet_result[1::2])
            )
            geo_issue = [
                {"issue_type": name.upper(), "count": count}
                for name, count in list(issue_dict.items())
            ]

        charts = {
            "taxon": {
                "family_counts": taibif_counts,
                "genus_counts": genus_counts,
                "top_taxa": top_taxa,
            },
            "location": {
                "latitude_percent": latitude_percent,
                "longitude_percent": longitude_percent,
            },
            "time": {"year_percent": year_percent},
            "issue": {"taxon": taxon_issue, "time": time_issue, "geo": geo_issue},
        }

    except Dataset.DoesNotExist:
        raise Http404("Dataset does not exist")

    return render(
        request,
        "dataset.html",
        {
            "dataset": dataset,
            "contacts": contacts,
            "citation": citation,
            "description": description,
            "keyword": keyword,
            "charts": charts,
        },
    )


def publisher_view(request, pk):
    publisher = get_object_or_404(DatasetOrganization, pk=pk)
    public_datasets = Dataset.objects.filter(organization_id=pk, status="PUBLIC")

    dataset = []
    for x in public_datasets:
        dataset.append(
            {
                "name": x.name,
                "name_zh": x.title or x.name,
                "core_type": DATA_MAPPING["publisher_dwc"].get(
                    x.dwc_core_type, x.dwc_core_type or "未知"
                ),
                "num_record": x.num_record or 0,
                "taibif_dataset_id": x.taibif_dataset_id,
            }
        )

    info_agg = public_datasets.aggregate(
        sum_occurrence=Sum("num_occurrence"),
        sum_record=Sum("num_record"),
    )
    context = {
        "publisher": publisher,
        "info": {
            "dataset_num": public_datasets.count(),
            "sum_occurrence": info_agg["sum_occurrence"] or 0,
            "sum_record": info_agg["sum_record"] or 0,
        },
        "dataset": dataset,
    }

    return render(request, "publisher.html", context)


# 地理分佈|資料集出現次數|物種描述|文獻
def species_view(request, taicol_taxon_id):
    context = {}
    dataset_data = []
    search_count = 0
    map_geojson = False
    taxon = get_object_or_404(Taxon, taicol_taxon_id=taicol_taxon_id)
    # switch = {
    #         'kingdom':'kingdom_key',
    #         'phylum':'phylum_key',
    #         'class':'class_key',
    #         'order':'order_key',
    #         'family':'family_key',
    #         'genus':'genus_key',
    #         'species':'taxon_id',
    #     }
    # total = []

    # 資料集出現次數資訊
    solr_q = f"path:{str(taicol_taxon_id)}"
    solr_facet = (
        "facet=true&facet.field=taibif_dataset_name_zh&facet.field=taibif_datasetKey"
    )
    solr_url = f"http://solr:8983/solr/taibif_occurrence/select?&q.op=AND&rows=0&q=basisOfRecord:*&fq={solr_q}&{solr_facet}"  # rows=0 since solr search results are not necessary for this page
    r = requests.get(solr_url)

    if r.status_code == 200:
        resp = r.json()
        search_count = resp["response"]["numFound"]
        data = resp["facet_counts"]["facet_fields"].get("taibif_dataset_name_zh", [])
        dataset_key = resp["facet_counts"]["facet_fields"].get("taibif_datasetKey", [])
        dataset_data = [
            {"count": count, "name_zh": name, "taibifDatasetID": key}
            for name, count, key in zip(data[::2], data[1::2], dataset_key[::2])
            if count > 0
        ]

    # map_url = "http://127.0.0.1/api/v2/occurrence/search?q=*:*&fq="+solr_q+"&facet=year&facet=month&facet=dataset&facet=dataset_id&facet=publisher&facet=country&facet=license"
    map_url = f"http://solr:8983/solr/taibif_occurrence/select?&q.op=AND&q=basisOfRecord:*&fq={solr_q}"
    # map_resp = get_geojson(map_url)
    # print(f'MAP RESP: {map_resp}')
    # r2 = requests.get(map_url)
    # print(f'MAP URL: {map_url}')
    # print(f'MAP RESP: {r2}')
    # if r2.status_code == 200:
    #     data2 = r2.json()

    # if data2['map_geojson']['features']!=[]:
    #     map_geojson = True

    # dataset_occ_count

    context = {
        "taxon": taxon,
        "dataset": dataset_data,
        "total": search_count,
        "map_view": True,
    }

    return render(request, "species.html", context)


def search_view(request, cat=""):

    context = {"env": settings.ENV}
    return render(request, "search.html", context)


def search_view_species(request, cat=""):

    context = {"env": settings.ENV}
    return render(request, "search_species.html", context)


def search_occurrence_download_view(request):
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # for dropna
    column_map = {}
    rows = []
    for i in RawDataOccurrence._meta.get_fields():
        if (
            not i.many_to_many
            and not i.one_to_one
            and not i.one_to_many
            and not i.many_to_one
        ):
            column_map[i.name] = {
                "title": i.db_column or i.verbose_name,
                "is_na": True,
            }
    occur_search = OccurrenceSearch(list(request.GET.lists()))

    ## very slow!
    # def raw_data_map(x):
    # d = {}
    # for col, col_data in column_map.items():
    #    if v := getattr(x.taibif, col):
    #        column_map[col]['na'] = False
    #        d[col] = v
    #   return x

    # override mod_search
    # occur_search.result_map = raw_data_map
    occur_search.limit = -1

    res = occur_search.get_results()

    taibif_ids = [x["taibif_id"] for x in res["results"]]
    raw_data_list = RawDataOccurrence.objects.filter(taibif_id__in=taibif_ids).all()

    rows = []
    for d in raw_data_list:
        r = {}
        for col, col_data in column_map.items():
            if v := getattr(d, col):
                column_map[col]["is_na"] = False
                r[col] = v
        rows.append(r)

    # prepare to csv
    csv_headers = []
    columns = []

    # get valid column and (not null)
    for col, col_data in column_map.items():
        if col_data["is_na"] == False and "taibif_" not in col:
            csv_headers.append(col_data["title"])
            columns.append(col)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="taibif-occurrence-{}.csv"'.format(date_str)
    )

    writer = csv.writer(response)
    writer.writerow(csv_headers)

    for d in raw_data_list:
        writer.writerow([getattr(d, col) for col in columns])

    return response
