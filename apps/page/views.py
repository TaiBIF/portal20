import re
import csv
import codecs
import json
import requests

import os
import environ
from django.shortcuts import render, get_object_or_404, redirect
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    JsonResponse,
)
from django.db.models import Q, F, Count, Sum, ExpressionWrapper, fields
from django.conf import settings
from django.contrib import messages
from apps.data.models import (
    Dataset,
    DatasetUpdateEvent,
    Taxon,
    DatasetOrganization,
)
from apps.article.models import Article
from apps.data.models import (
    WorkshopCertificationList,
    TaibifParticipants,
    TaibiferList,
    DataPaperList,
    Taibifer,
)
from .models import Post, Journal, IndexBubbleSetting
from .models import NewsletterSubscription
from utils.mail import taibif_mail_contact_us

from apps.data.helpers.stats import get_home_stats
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.utils.translation import activate
from django.utils import timezone
from collections import defaultdict
from django.core.paginator import Paginator


def act_lang(func):
    def wrapper(*args, **kwargs):
        activate("zh-hant")  # default 中文
        resp = func(*args, **kwargs)
        return resp

    return wrapper


# @act_lang
def index(request):
    article_qs = Article.objects.filter(category__in=["NEWS", "EVENT", "SCI"]).order_by(
        "-is_pinned", "-created"
    )

    category_map = {"NEWS": [], "EVENT": [], "SCI": []}
    news_all_list = []
    for article in article_qs:
        if len(news_all_list) < 4:
            news_all_list.append(article)

        if article.category in category_map and len(category_map[article.category]) < 4:
            category_map[article.category].append(article)

        if len(news_all_list) >= 12 and all(
            len(category_map[key]) >= 4 for key in ("NEWS", "EVENT", "SCI")
        ):
            break

    news_list = category_map["NEWS"]
    event_list = category_map["EVENT"]
    update_list = category_map["SCI"]

    story_list = Article.objects.filter(category="STORY").order_by("-created").all()[:6]

    def assign_card_image(articles):
        # Priority: cover image > media_url > fallback image.
        for article in articles:
            if article.cover:
                article.card_image_url = article.cover.url
                continue

            if article.media_url:
                media_url = article.media_url.strip()
                if media_url.startswith("http://") or media_url.startswith("https://"):
                    article.card_image_url = media_url
                else:
                    article.card_image_url = (
                        f"{settings.MEDIA_URL}{media_url.lstrip('/')}"
                    )
                continue

            article.card_image_url = f"{settings.STATIC_URL}taibif-home/image/ubpic.jpg"

    assign_card_image(news_all_list)
    assign_card_image(news_list)
    assign_card_image(event_list)
    assign_card_image(update_list)
    assign_card_image(story_list)

    url = f"http://solr:8983/solr/taibif_occurrence/select?q=basisOfRecord:*&fq=selfProduced:true&indent=true&q.op=OR&rows=0"
    r = requests.get(url).json()
    occ_num = r["response"]["numFound"]

    dataset_num = Dataset.objects.filter(status="PUBLIC", source="TaiBIF IPT").count()

    taxon_num = Taxon.objects.values("name").distinct().count()

    # taxonGroup_url = f"http://solr:8983/solr/taibif_occurrence/select?basisOfRecord:*&facet.field=taibif_taxonGroup&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0"
    # taxonGroup_r = requests.get(taxonGroup_url).json()
    # taibif_taxonGroup = taxonGroup_r["facet_counts"]["facet_fields"][
    #     "taibif_taxonGroup"
    # ]

    # taxonGroup_keys_list = taibif_taxonGroup[::2]
    # taxonGroup_values_list = taibif_taxonGroup[1::2]
    # taxonGroup_dict = dict(zip(taxonGroup_keys_list, taxonGroup_values_list))

    # # Merge group archaea with group others
    # if "Others" in taxonGroup_dict and "Archaea" in taxonGroup_dict:
    #     taxonGroup_dict["Others"] += taxonGroup_dict["Archaea"]
    #     del taxonGroup_dict["Archaea"]

    publisher_num = DatasetOrganization.objects.count()

    gbif_data_case_url = (
        "https://api.gbif.org/v1/literature/search?countriesOfCoverage=TW"
    )
    gbif_data_case_response = requests.get(gbif_data_case_url)
    if gbif_data_case_response.status_code == 200:
        gbif_data_case_dict = gbif_data_case_response.json()
        if gbif_data_case_dict:
            gbif_data_case_count = gbif_data_case_dict["count"]
        else:
            gbif_data_case_count = 0
    else:
        gbif_data_case_count = 0

    taibif_case_count = Article.objects.filter(is_data_case=True).count()
    total_case_count = gbif_data_case_count + taibif_case_count
    index_bubble = IndexBubbleSetting.get_solo()

    occ_num_display = f"{occ_num:,}"
    dataset_num_display = f"{dataset_num:,}"
    taxon_num_display = f"{taxon_num:,}"
    publisher_num_display = f"{publisher_num:,}"
    case_count_display = f"{total_case_count:,}"

    context = {
        "news_all_list": news_all_list,
        "news_list": news_list,
        "event_list": event_list,
        "update_list": update_list,
        "story_list": story_list,
        # "stats": get_home_stats(),
        "dataset_num": dataset_num,
        "occ_num": occ_num,
        "taxon_num": taxon_num,
        "occ_num_display": occ_num_display,
        "dataset_num_display": dataset_num_display,
        "taxon_num_display": taxon_num_display,
        # "taxonGroup_dict": taxonGroup_dict,
        "publisher_num": publisher_num,
        "case_count": total_case_count,
        "publisher_num_display": publisher_num_display,
        "case_count_display": case_count_display,
        "index_bubble": index_bubble,
    }

    return render(request, "index.html", context)


# @act_lang
def publishing_data(request):
    return render(request, "publishing-data.html")


# @act_lang
def data_policy(request):
    return render(request, "data-policy.html")


# @act_lang
def journals(request):
    Journal_url = Journal.objects.all()

    return render(request, "journals.html", locals())


# @act_lang
def cookbook(request):
    return render(request, "cookbook.html")


# @act_lang
def cookbook_detail_1(request):
    return render(request, "cookbook-detail-1.html")


# @act_lang
def cookbook_detail_2(request):
    return render(request, "cookbook-detail-2.html")


# @act_lang
def cookbook_detail_3(request):
    return render(request, "cookbook-detail-3.html")


# @act_lang
def tools(request):
    return render(request, "tools.html")


def coordinate_converter(request):
    return render(request, "coordinate-converter.html")


def coordinate_converter_legacy(request):
    return redirect("coordinate-converter", permanent=True)


@require_POST
def newsletter_subscribe(request):
    email = (request.POST.get("email") or "").strip().lower()
    confirm_email = (request.POST.get("confirm_email") or "").strip().lower()

    if not email or not confirm_email:
        return JsonResponse({"ok": False, "message": "請填寫電子信箱與確認信箱。"}, status=400)

    if email != confirm_email:
        return JsonResponse({"ok": False, "message": "兩次輸入的電子信箱不一致。"}, status=400)

    email_validator = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    if not email_validator.match(email):
        return JsonResponse({"ok": False, "message": "電子信箱格式不正確。"}, status=400)

    _, created = NewsletterSubscription.objects.get_or_create(email=email)
    if created:
        return JsonResponse({"ok": True, "message": "已成功訂閱電子報。"})
    return JsonResponse({"ok": True, "message": "此信箱已在訂閱名單中。"})


# @act_lang
def contact_us(request):
    if request.method == "GET":
        return render(request, "contact-us.html")
    elif request.method == "POST":
        """Begin reCAPTCHA validation"""
        recaptcha_response = request.POST.get("h-captcha-response")
        # print(recaptcha_response)
        data = {"secret": settings.HCAPTCHA_SECRET_KEY, "response": recaptcha_response}
        r = requests.post("https://hcaptcha.com/siteverify", data=data)
        result = r.json()
        """ End reCAPTCHA validation """

        if result["success"] == False:
            messages.error(request, "請進行驗證，謝謝")
            return redirect("contact_us")

        if re.search("\?", request.POST.get("cat", "")):
            messages.error(request, "請進行驗證，謝謝")
            return redirect("contact_us")

        data = {
            "name": request.POST.get("name", ""),
            "cat": request.POST.get("cat", ""),
            "email": request.POST.get("email", ""),
            "content": request.POST.get("content", ""),
        }
        context = taibif_mail_contact_us(data)
        # context = taibif_send_mail(subject, content, settings.SERVICE_EMAIL, to_list)

        return render(request, "contact-us.html", context)


@act_lang
def plans(request):
    return render(request, "plans.html")


# @act_lang
def links(request):
    Post_url = Post.objects.all()
    return render(request, "links.html", locals())


# @act_lang
def about_taibif(request):
    achievement_qs = Article.objects.filter(category="POS").order_by("-created")
    achievement_years = sorted(
        set(achievement_qs.values_list("created__year", flat=True)),
        reverse=True,
    )

    selected_year = request.GET.get("achievement_year", "")
    if selected_year:
        achievement_qs = achievement_qs.filter(created__year=selected_year)

    paginator = Paginator(achievement_qs, 20)
    achievements_page = paginator.get_page(request.GET.get("page", ""))

    context = {
        "achievement_years": achievement_years,
        "achievement_year": selected_year,
        "achievements_page": achievements_page,
    }
    return render(request, "about-taibif.html", context)


# @act_lang
def about_gbif(request):
    return render(request, "about-gbif.html")


# @act_lang
def open_data(request):
    return render(request, "open-data.html")


# @act_lang
def data_stats(request):
    most = request.GET.get("most", "")
    search_query = request.GET.get("search_query", "")
    # print(f'search_query:{search_query}')

    query = Dataset.objects
    if most:
        query = query.filter(is_most_project=True)
    # url = f"http://solr:8983/solr/taibif_occurrence/select?q=basisOfRecord:*&indent=true&q.op=OR&rows=0"
    # r = requests.get(url).json()
    # occ_num = r["response"]["numFound"]

    # dataset_num = Dataset.objects.filter(status="PUBLIC", source="TaiBIF IPT").count()
    # publisher_num = DatasetOrganization.objects.count()

    dataset_orm = Dataset.objects.filter(source="TaiBIF IPT", status="PUBLIC").order_by(
        "-pub_date"
    )
    # Grab the content for the table
    if search_query:
        dataset = dataset_orm.filter(
            Q(title__contains=search_query) | Q(dwc_core_type__contains=search_query)
        ).values(
            "title",
            "organization_name",
            "dwc_core_type",
            "num_occurrence",
            "num_record",
            "pub_date",
            "country",
            "status",
            "is_most_project",
            "taibif_dataset_id",
        )
    else:
        dataset = dataset_orm.values(
            "title",
            "organization_name",
            "dwc_core_type",
            "num_occurrence",
            "num_record",
            "pub_date",
            "country",
            "status",
            "is_most_project",
            "taibif_dataset_id",
        )

    if most == "1":
        dataset = dataset.filter(is_most_project=True)

    value_mapping = {
        "OCCURRENCE": "出現紀錄",
        "SAMPLINGEVENT": "調查活動",
        "CHECKLIST": "物種名錄",
        "metadata": "詮釋資料",
    }

    modified_dataset = []

    for item in dataset:
        item["dwc_core_type"] = value_mapping.get(
            item["dwc_core_type"], item["dwc_core_type"]
        )
        modified_dataset.append(item)

    gbif_data_case_url = (
        "https://api.gbif.org/v1/literature/search?countriesOfCoverage=TW"
    )
    gbif_data_case_response = requests.get(gbif_data_case_url)
    if gbif_data_case_response.status_code == 200:
        gbif_data_case_dict = gbif_data_case_response.json()
        if gbif_data_case_dict:
            gbif_data_case_count = gbif_data_case_dict["count"]
        else:
            gbif_data_case_count = 0
    else:
        gbif_data_case_count = 0

    taibif_case_count = Article.objects.filter(is_data_case=True).count()
    total_case_count = gbif_data_case_count + taibif_case_count

    context = {
        "dataset_list": query.order_by(F("pub_date").desc(nulls_last=True)).all(),
        # "dataset_num": dataset_num,
        # "publisher_num": publisher_num,
        # "occ_num": occ_num,
        "env": settings.ENV,
        "dataset": modified_dataset,
        "case_count": total_case_count,
    }
    return render(request, "data-stats.html", context)


def common_name_checker(request):
    global results
    if request.method == "GET":
        q = request.GET.get("q", "")
        sep = request.GET.get("sep", "")
        context = {
            "q": q,
            "sep": sep,
        }
        return render(request, "tools-common_name_checker.html", context)
    elif request.method == "POST":

        q = request.POST.get("q", "")
        sep = request.POST.get("sep", "n")

        if not q:
            context = {
                "message": {
                    "head": "輸入錯誤",
                    "content": "請輸入中文名",
                }
            }
            return render(request, "tools-common_name_checker.html", context)

        if q in ["台灣", "臺灣"]:
            context = {
                "message": {
                    "head": "結果太多",
                    "content": "請輸入更完整中文名",
                },
                "sep": sep,
                "q": q,
            }
            return render(request, "tools-common_name_checker.html", context)

        if not sep:
            sep = "n"
        results = []
        if sep not in [",", "n"]:
            return HttpResponseNotFound("err input")

        sep_real = "\n" if sep == "n" else sep
        cname_list = q.split(sep_real)
        cname_list = list(set(cname_list))

        # taiwan_char_check_exclude = ['台灣留鳥', '台灣過境', '台灣亞種', '台灣特有亞種']
        for cn in cname_list:
            cn = cn.strip()

            q_replace = ""
            if "台灣" in cn:
                q_replace = cn.replace("台灣", "臺灣")

            if "臺灣" in cn:
                q_replace = cn.replace("臺灣", "台灣")

            row = {"common_name": cn, "match_type": "no match", "match_list": []}
            taxa = Taxon.objects.filter(rank="species")
            if q_replace:
                row["q_replace"] = q_replace
                taxa = Taxon.objects.filter(
                    Q(name_zh__icontains=cn) | Q(name_zh__icontains=q_replace)
                ).all()
            else:
                taxa = Taxon.objects.filter(name_zh__icontains=cn).all()

            if taxa:
                row["match_type"] = "match"

            for t in taxa:
                row["match_list"].append(t)
            results.append(row)

        context = {
            "results": results,
            "q": q,
            "sep": sep,
        }
        if "export_csv" in request.POST:
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="users.csv"'
            response.write(codecs.BOM_UTF8)

            writer = csv.writer(response)
            print(request)

            for row in results:
                writer.writerow(row["match_list"])

            return response
    return render(request, "tools-common_name_checker.html", context)


def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'
    response.write(codecs.BOM_UTF8)

    writer = csv.writer(response)
    print(request)

    for row in results:
        writer.writerow(row["match_list"])

    return response


def taibif_achievement(request):
    context = {}
    return render(request, "taibif-achievement.html", context)


def faq(request):
    context = {}
    return render(request, "faq.html", context)


def download_resources(request):
    context = {}
    return render(request, "download-resources.html", context)


def thanks_list(request):
    participants_list = TaibifParticipants.objects.values("name", "role", "missions")
    taibifer_list = TaibiferList.objects.values("name", "role", "missions")

    context = {"participants": participants_list, "taibifers": taibifer_list}
    return render(request, "thanks-list.html", context)


def open_process(request):
    context = {}
    return render(request, "open-process.html", context)


def open_standard(request):
    context = {}
    return render(request, "open-standard.html", context)


def open_metadata(request):
    context = {}
    return render(request, "open-metadata.html", context)


def open_uplaod(request):
    context = {}
    return render(request, "open-upload.html", context)


def open_license(request):
    context = {}
    return render(request, "open-license.html", context)


def open_timezone(request):
    context = {}
    return render(request, "open-timezone.html", context)


def tech_open(request):
    context = {}
    return render(request, "tech-open.html", context)


def tech_book(request):
    context = {}
    return render(request, "tech-book.html", context)


def tech_workshop(request):
    context = {}
    return render(request, "tech-workshop.html", context)


def tech_online_class(request):
    context = {}
    return render(request, "tech-online-class.html", context)


def tech_class_license(request):
    certification_list = WorkshopCertificationList.objects.all().order_by("year")
    certification_data = {}
    for item in certification_list:
        year = item.year
        level = item.level
        name = item.name

        if year not in certification_data:
            certification_data[year] = {"basic": [], "advanced": []}

        if level == "basic":
            certification_data[year]["basic"].append(name)
        elif level == "advanced":
            certification_data[year]["advanced"].append(name)
    sorted_certification_data = dict(
        sorted(certification_data.items(), key=lambda item: item[0], reverse=True)
    )
    context = {"certification_data": sorted_certification_data}
    return render(request, "tech-class-license.html", context)


def tech_volunteer(request):
    taibifer_entries = Taibifer.objects.prefetch_related("roles").order_by("-year")

    grouped_by_roles = {}
    for entry in taibifer_entries:
        for role in entry.roles.all():
            if role.name not in grouped_by_roles:
                grouped_by_roles[role.name] = {}
            if entry.year not in grouped_by_roles[role.name]:
                grouped_by_roles[role.name][entry.year] = []
            grouped_by_roles[role.name][entry.year].append(entry.name)
    context = {"grouped_taibifer": grouped_by_roles}
    return render(request, "tech-volunteer.html", context)


def data_paper(request):
    data_paper_list = (
        DataPaperList.objects.all().order_by("-year", "-last_update").values()
    )
    latest_update = (
        data_paper_list.last()["last_update"].strftime("%Y/%m/%d")
        if data_paper_list
        else None
    )
    journals = Journal.objects.all().order_by("sort").values()
    context = {
        "data_paper_list": data_paper_list,
        "latest_update": latest_update,
        "journals": journals,
    }
    return render(request, "data-paper.html", context)


def data_visual(request):
    taxonGroup_url = f"http://solr:8983/solr/taibif_occurrence/select?facet.field=taibif_taxonGroup&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0"
    taxonGroup_r = requests.get(taxonGroup_url).json()
    taibif_taxonGroup = taxonGroup_r["facet_counts"]["facet_fields"][
        "taibif_taxonGroup"
    ]
    taxonGroup_keys_list = taibif_taxonGroup[::2]
    taxonGroup_values_list = taibif_taxonGroup[1::2]
    taxonGroup_dict = dict(zip(taxonGroup_keys_list, taxonGroup_values_list))

    # Merge group archaea with group others
    if "Others" in taxonGroup_dict and "Archaea" in taxonGroup_dict:
        taxonGroup_dict["Others"] += taxonGroup_dict["Archaea"]
        del taxonGroup_dict["Archaea"]
    context = {
        "taxonGroup_dict": taxonGroup_dict,
    }
    return render(request, "data-visual.html", context)


def data_case(request):
    articles = (
        Article.objects.filter(is_data_case=True, category="SCI")
        .order_by("-created")
        .select_related("new_case_type")[:3]
    )  # 只選最新三筆呈現

    results = []
    for article in articles:
        formatted_date = article.created.strftime("%Y/%m/%d")
        case_type_name = article.new_case_type.name if article.new_case_type else ""
        results.append(
            {
                "id": article.id,
                "date": formatted_date,
                "title": article.title,
                "case_type": case_type_name,
                "content": article.summary,
            }
        )

    context = {"articles": results}
    return render(request, "data-case.html", context)


def data_product(request):
    context = {}
    return render(request, "data-product.html", context)


def data_story(request):
    context = {}
    return render(request, "data-story.html", context)


def data_clean(request):
    return render(
        request,
        "data-clean.html",
    )


def web_navi(request):
    context = {}
    return render(request, "web-navi.html", context)


def trans(request):
    translate_str = _("這裡放需要翻譯的文字")
    context = {"translate_str": translate_str}
    return render(request, "index.html", context)


@require_GET
def robots_txt(request):

    if os.environ.get("ENV") == "prod":
        lines = [
            "User-Agent: *",
            "Disallow: /admin/",
        ]

        return HttpResponse("\n".join(lines), content_type="text/plain")

    else:
        lines = [
            "User-Agent: *",
            "Disallow: /",
        ]

        return HttpResponse("\n".join(lines), content_type="text/plain")


## Kuan-Yu added for API occurence record


@act_lang
def taibif_api(request):
    return render(request, "taibif-api.html")


def page_not_found_view(request, exception=None):
    return render(request, "404.html", status=404)


def response_error_handler(request, exception=None):
    return render(request, "500.html", status=500)


def open_consulation(request):
    return render(request, "open-consulation.html")


def open_benefits(request):
    return render(request, "open-benefits.html")


def monthly_status(request):
    today = timezone.localdate()
    current_year = today.year
    current_month = today.month

    try:
        selected_year = int(request.GET.get("year", current_year))
    except (TypeError, ValueError):
        selected_year = current_year

    try:
        selected_month = int(request.GET.get("month", current_month))
    except (TypeError, ValueError):
        selected_month = current_month

    if selected_month < 1 or selected_month > 12:
        selected_month = current_month

    core_type_mapping = {
        "CHECKLIST": "物種名錄",
        "OCCURRENCE": "出現紀錄",
        "SAMPLINGEVENT": "調查活動",
        "METADATA": "詮釋資料",
        "metadata": "詮釋資料",
    }

    event_queryset = DatasetUpdateEvent.objects.all()

    available_years = list(
        event_queryset.values_list("dataset_mod_date__year", flat=True)
        .distinct()
        .order_by("-dataset_mod_date__year")
    )
    if not available_years:
        available_years = [current_year]

    monthly_events = (
        event_queryset.filter(
            dataset_mod_date__year=selected_year,
            dataset_mod_date__month=selected_month,
        )
        .values(
            "dataset_id",
            "dataset_title",
            "dataset_name",
            "dwc_core_type",
            "organization_name",
            "taibif_dataset_id",
            "dataset_mod_date",
        )
        .order_by("-dataset_mod_date", "dataset_name")
    )

    # Keep only the latest event per dataset in the selected month.
    dataset_latest_event_map = {}
    for event in monthly_events:
        if event["dataset_id"] not in dataset_latest_event_map:
            dataset_latest_event_map[event["dataset_id"]] = event

    dataset_ids = list(dataset_latest_event_map.keys())
    dataset_org_map = dict(
        Dataset.objects.filter(id__in=dataset_ids).values_list("id", "organization_id")
    )

    dataset_rows = []
    for event in dataset_latest_event_map.values():
        publisher_id = dataset_org_map.get(event["dataset_id"])
        dataset_rows.append(
            {
                "title": event["dataset_title"] or event["dataset_name"],
                "dwc_core_type": core_type_mapping.get(
                    event["dwc_core_type"], event["dwc_core_type"]
                ),
                "organization_name": event["organization_name"] or "－",
                "publisher_id": publisher_id,
                "taibif_dataset_id": event["taibif_dataset_id"],
                "ipt_link": f"https://ipt.taibif.tw/resource?r={event['dataset_name']}",
            }
        )

    context = {
        "selected_year": selected_year,
        "selected_month": selected_month,
        "selected_month_label": f"{selected_year:04d}-{selected_month:02d}",
        "available_years": available_years,
        "available_months": list(range(1, 13)),
        "dataset_rows": dataset_rows,
    }
    return render(request, "monthly-status.html", context)
