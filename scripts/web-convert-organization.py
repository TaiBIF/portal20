
from apps.data.models import Dataset, DatasetOrganization

orgs = []
for i in Dataset.objects.all():
    o = i.organization_verbatim
    if o and o not in orgs:
        orgs.append(o)

#print (orgs)
#for i in  orgs:
#    do = DatasetOrganization(
#        name=i
#    )
#    do.save()

org_map = {}
for i in DatasetOrganization.objects.all():
    print (i.id, i.name)
    org_map[i.name] = i.id
print (org_map)
for i in Dataset.objects.all():
    if i.organization_verbatim:
        i.organization_id = org_map[i.organization_verbatim]
    i.save()
