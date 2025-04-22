from datetime import datetime
from apps.data.models import Dataset
from apps.article.models import Article
from django.utils.text import slugify

CORE_TYPE_MAPPING = {
    "CHECKLIST": f'<a class="checklist-highlight-link" href="/dataset/search/?core=CHECKLIST" target="_blank">物種名錄</a>',
    "OCCURRENCE": f'<a class="occurrence-highlight-link" href="/dataset/search/?core=OCCURRENCE" target="_blank">出現紀錄</a>',
    "SAMPLINGEVENT": f'<a class="samplingevent-highlight-link" href="/dataset/search/?core=SAMPLINGEVENT" target="_blank">調查活動</a>',
    "METADATA": f'<a class="metadata-highlight-link" href="/dataset/search/?core=METADATA" target="_blank">詮釋資料</a>',
}

current_year = datetime.now().year
current_month = datetime.now().month

updated_dataset_this_month = Dataset.objects.filter(
    source="TaiBIF IPT",
    status="PUBLIC",
    mod_date__year=current_year,
    mod_date__month=current_month,
).all()

if not updated_dataset_this_month:
    print(f"{current_year}-{current_month} 沒有任何新的公開資料集更新，文章未建立。")
else:
    slug = slugify(f"{current_year}年{current_month}月TaiBIF更新", allow_unicode=True)

    if Article.objects.filter(slug=slug).exists():
        print(f"{current_year}-{current_month} 的更新文章已存在，未重複建立。")
    else:
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

        for dataset in updated_dataset_this_month:
            taibif_link = f"/dataset/{dataset.taibif_dataset_id}"
            ipt_link = f"https://ipt.taibif.tw/resource?r={dataset.name}"
            row_html = f"""
                <tr>
                    <td><a class="highlight-link" href="{taibif_link}" target="_blank">{dataset.title}</a></td>
                    <td>{CORE_TYPE_MAPPING.get(dataset.dwc_core_type, dataset.dwc_core_type)}</td>
                    <td>{dataset.organization_name or '－'}</td>
                    <td><a class="highlight-link" href="{ipt_link}" target="_blank">連結</a></td>
                </tr>
            """
            table_html += row_html

        table_html += """
                </tbody>
            </table>
        </div>
        """

        article_content = f"""
        <h2>TaiBIF 本月資料更新總覽（{current_year} 年 {current_month} 月）</h2>
        <p>🎉 本月 TaiBIF 平台又有新氣象啦！</p>
        <p>以下是來自 TaiBIF IPT 的資料來源中，標記為公開（PUBLIC）並在這個月有「上傳」或「更新」的資料集✨</p>
        <p>我們一共整理了 {len(updated_dataset_this_month)} 筆資料集，主題多元、內容豐富，等你來探索 📚🔍</p>
        <p>趕快來看看這些本月的新鮮資料吧👇👇</p>
        {table_html}
        """

        article = Article(
            title=f"{current_year} 年 {current_month} 月 TaiBIF 資料集更新總覽",
            summary=f"{current_month} 月 TaiBIF 平台共更新了 {len(updated_dataset_this_month)} 筆資料集。",
            content=article_content,
            slug=slug,
            created=datetime.now(),
            changed=datetime.now(),
            category="NEWS",
            is_pinned="N",
            is_homepage=False,
            is_content_markdown=False,
            is_data_case=False,
        )
        article.save()

        print(f"{current_year}-{current_month} 資料集文章成功發佈")
