from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional

from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.text import slugify
from django.utils.translation import override

from apps.article.models import Article
from apps.data.models import DatasetUpdateEvent


CORE_TYPE_MAPPING = {
    "CHECKLIST": '<div class="checklist-highlight-link">物種名錄</div>',
    "OCCURRENCE": '<div class="occurrence-highlight-link">出現紀錄</div>',
    "SAMPLINGEVENT": '<div class="samplingevent-highlight-link">調查活動</div>',
    "METADATA": '<div class="metadata-highlight-link">詮釋資料</div>',
}


@dataclass
class PublishDatasetArticleResult:
    status: str
    year: int
    month: int
    dataset_count: int
    message: str
    article: Optional[Article] = None


def previous_month(reference_date=None):
    reference_date = reference_date or timezone.localdate()
    if reference_date.month == 1:
        return reference_date.year - 1, 12
    return reference_date.year, reference_date.month - 1


def month_range(year, month):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(datetime(year, month, 1), time.min), tz)
    end_day = monthrange(year, month)[1]
    end = timezone.make_aware(
        datetime.combine(datetime(year, month, end_day), time.max),
        tz,
    )
    return start, end


def build_dataset_article_content(events):
    table_html = """
    <div class="article-table-container">
        <table class="table dataset-table">
            <thead>
                <tr>
                    <th>資料集名稱</th>
                    <th>資料集類型</th>
                    <th>發布單位</th>
                    <th>IPT 頁面</th>
                </tr>
            </thead>
            <tbody>
    """

    for event in events:
        dataset_title = event["dataset_title"] or event["dataset_name"]
        taibif_link = f"/dataset/{event['taibif_dataset_id']}"
        ipt_link = f"https://ipt.taibif.tw/resource?r={event['dataset_name']}"
        core_type = CORE_TYPE_MAPPING.get(
            event["dwc_core_type"],
            escape(event["dwc_core_type"] or "－"),
        )
        row_html = f"""
            <tr>
                <td><a class="highlight-link" href="{taibif_link}" target="_blank">{escape(dataset_title)}</a></td>
                <td>{core_type}</td>
                <td>{escape(event["organization_name"] or '－')}</td>
                <td><a class="highlight-link" href="{ipt_link}" target="_blank">連結</a></td>
            </tr>
        """
        table_html += row_html

    table_html += """
            </tbody>
        </table>
    </div>
    """

    with override("zh-hant"):
        monthly_status_url = reverse("monthly-status")

    return f"""
    <p>🎉 本月 TaiBIF 平台又有新氣象啦！</p>
    <p>以下是透過 TaiBIF IPT 發布，並在這個月有「上傳」或「更新」的資料集✨</p>
    <p>我們一共整理了 {len(events)} 筆資料集，主題多元、內容豐富，等你來探索 📚🔍</p>
    <p>趕快來看看這些本月的新鮮資料吧👇👇</p>
    {table_html}
    <div class="content-readable-panel">若想查看各月份的資料集更新歷程，可以利用 <a href="{monthly_status_url}" rel="noopener noreferrer">每月資料發布狀況</a> 頁面。</div>
    """


def publish_dataset_article(year, month, *, force=False, created_at=None):
    start, end = month_range(year, month)
    monthly_events = (
        DatasetUpdateEvent.objects.filter(
            source="TaiBIF IPT",
            status="PUBLIC",
            dataset_mod_date__gte=start,
            dataset_mod_date__lte=end,
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

    latest_event_by_dataset = {}
    for event in monthly_events:
        if event["dataset_id"] not in latest_event_by_dataset:
            latest_event_by_dataset[event["dataset_id"]] = event

    events = sorted(
        latest_event_by_dataset.values(),
        key=lambda event: (
            event["organization_name"] or "",
            event["dataset_title"] or event["dataset_name"] or "",
        ),
    )

    if not events:
        return PublishDatasetArticleResult(
            status="skipped",
            year=year,
            month=month,
            dataset_count=0,
            message=f"{year}-{month:02d} 沒有任何新的公開資料集更新，文章未建立。",
        )

    slug = slugify(f"{year}年{month}月TaiBIF更新", allow_unicode=True)
    existing_article = Article.objects.filter(slug=slug).first()

    if existing_article and not force:
        return PublishDatasetArticleResult(
            status="exists",
            year=year,
            month=month,
            dataset_count=len(events),
            message=f"{year}-{month:02d} 的更新文章已存在，未重複建立。",
            article=existing_article,
        )

    now = timezone.now()
    article_values = {
        "title": f"{year} 年 {month} 月 TaiBIF 資料集更新總覽",
        "summary": f"{month} 月 TaiBIF 平台共更新了 {len(events)} 筆資料集。",
        "content": build_dataset_article_content(events),
        "created": created_at or now,
        "changed": now,
        "category": "NEWS",
        "is_pinned": "N",
        "is_homepage": False,
        "is_content_markdown": False,
        "is_data_case": False,
    }

    if existing_article:
        for field, value in article_values.items():
            setattr(existing_article, field, value)
        existing_article.save()
        return PublishDatasetArticleResult(
            status="updated",
            year=year,
            month=month,
            dataset_count=len(events),
            message=f"{year}-{month:02d} 資料集文章已重新產生。",
            article=existing_article,
        )

    article = Article.objects.create(slug=slug, **article_values)
    return PublishDatasetArticleResult(
        status="created",
        year=year,
        month=month,
        dataset_count=len(events),
        message=f"{year}-{month:02d} 資料集文章成功發布。",
        article=article,
    )
