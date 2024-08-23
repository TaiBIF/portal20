from django.contrib import admin

from .models import Taxon, Dataset, WorkshopCertificationList, TaibifParticipants, TaibiferList, DataPaperList, DatasetOrganization

class DatasetAdmin(admin.ModelAdmin):
    model = Dataset
    list_display = ('title', 'name', 'num_occurrence', 'pub_date', 'guid')
    list_filter = ('is_most_project', 'dwc_core_type', 'has_publish_problem')
    fields = ('title', 'name', 'author', 'pub_date', 'guid', 'dwc_core_type',  'num_occurrence',  'is_most_project', 'has_publish_problem', 'admin_memo')
    readonly_fields = ('title', 'name', 'author', 'pub_date', 'guid', 'dwc_core_type',  'num_occurrence', )
    search_fields = ('title',)


class TaxonAdmin(admin.ModelAdmin):
    model = Taxon
    # list_filter = ('rank')
    list_display = ('name', 'name_zh', 'rank', 'parent', 'count')
    fields = (('parent','parent_id'), 'name', 'name_zh', 'rank', 'count')
    readonly_fields = ('count', 'parent', 'parent_id')
    search_fields = ('name', 'name_zh')

class WorkshopCertificationListAdmin(admin.ModelAdmin):
    model = WorkshopCertificationList
    list_display = ('name', 'year', 'level', 'last_update')
    list_filter = ('year', 'level')
    fields = ('name', 'year', 'level')
    readonly_fields = ('last_update',)
    search_fields = ('name', 'year', 'level')

class TaibifParticipantsAdmin(admin.ModelAdmin):
    model = TaibifParticipants
    list_display = ('name', 'role', 'missions', 'last_update')
    list_filter = ('role', 'missions')
    fields = ('name', 'role', 'missions')
    readonly_fields = ('last_update',)
    search_fields = ('name', 'role', 'missions')

class TaibiferListAdmin(admin.ModelAdmin):
    model = TaibiferList
    list_display = ('name', 'role', 'missions', 'last_update')
    list_filter = ('role', 'missions')
    fields = ('name', 'role', 'missions')
    readonly_fields = ('last_update',)
    search_fields = ('name', 'role', 'missions')

class DataPaperListAdmin(admin.ModelAdmin):
    model = DataPaperList
    list_display = ('title', 'journal', 'article_doi', 'dataset_doi', 'year')
    list_filter = ('journal', 'year')
    fields = ('title', 'journal', 'article_doi', 'dataset_doi', 'year')
    readonly_fields = ('last_update',)
    search_fields = ('title', 'journal', 'article_doi', 'dataset_doi')

class DatasetOrganizationAdmin(admin.ModelAdmin):
    model = DatasetOrganization
    list_display = ('name', 'country_code', 'organization_gbif_uuid')
    list_filter = ('country_code',)
    fields = ('id', 'name', 'organization_gbif_uuid', 'description', 'country_code', 'country_or_area', 'administrative_contact', 'technical_contact', 'endorsed_by', 'installations', 'dataset_num', 'occurences_num')
    readonly_fields = ('id', 'dataset_num', 'occurences_num')
    search_fields = ('name', 'organization_gbif_uuid')


admin.site.register(Taxon, TaxonAdmin)
admin.site.register(Dataset, DatasetAdmin)
admin.site.register(WorkshopCertificationList, WorkshopCertificationListAdmin)
admin.site.register(TaibifParticipants, TaibifParticipantsAdmin)
admin.site.register(TaibiferList, TaibiferListAdmin)
admin.site.register(DataPaperList, DataPaperListAdmin)
admin.site.register(DatasetOrganization, DatasetOrganizationAdmin)
