from django.contrib import admin

from .models import Taxon, TaxonTree, Dataset

class DatasetAdmin(admin.ModelAdmin):
    model = Dataset
    list_display = ('title', 'name', 'num_occurrence', 'pub_date', 'guid')
    list_filter = ('is_most_project', 'dwc_core_type', 'has_publish_problem')
    fields = ('title', 'name', 'author', 'pub_date', 'guid', 'dwc_core_type',  'num_occurrence',  'is_most_project', 'has_publish_problem', 'admin_memo')
    readonly_fields = ('title', 'name', 'author', 'pub_date', 'guid', 'dwc_core_type',  'num_occurrence', )
    search_fields = ('title',)


class TaxonAdmin(admin.ModelAdmin):
    model = Taxon
    list_filter = ('rank','tree')
    list_display = ('name', 'name_zh', 'rank', 'parent', 'count', 'tree')
    fields = (('parent','parent_id'), 'name', 'name_zh', 'rank', 'count', 'tree')
    readonly_fields = ('count', 'parent', 'parent_id')
    search_fields = ('name', 'name_zh')

class TaxonTreeAdmin(admin.ModelAdmin):
    model = TaxonTree
    list_display = ('name',)
    fields = ('name', 'rank_map')


admin.site.register(Taxon, TaxonAdmin)
admin.site.register(TaxonTree, TaxonTreeAdmin)
admin.site.register(Dataset, DatasetAdmin)
