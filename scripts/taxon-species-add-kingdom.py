#!/usr/bin/env python
# -.- coding: utf-8 -.-

from apps.data.models import Taxon

count = 0
for i in Taxon.objects.order_by('id').all():
    count += 1
    i.hierarchy_string = '-'.join([str(x.id) for x in i.rank_list])
    if count % 1000 == 0:
        print (count)
