import time
#import timeit
import decimal
import pickle



#rows = RawDataOccurrence.objects.order_by('taibif_id').all()[:1000000]
#rows = RawDataOccurrence.objects.order_by('taibif_id').all()[390000:395000]
chunk_size = 100000 # 一次 10 筆
chunk_num = 50
chunk_num_begin = 0
def _get_taxon(rank, name):
    from apps.data.models import Taxon
    return Taxon.objects.filter(rank=rank, name=name).first()

start_time = time.time()

all_data = RawDataOccurrence.objects.values('taibif_id', 'taibif_dataset_name','year', 'month', 'day','country', 'decimallongitude', 'decimallatitude', 'kingdom', 'phylum', 'class_field', 'order', 'family', 'genus', 'scientificname', 'specificepithet').order_by('taibif_id').all()


tree = TaxonTree.objects.get(pk=1)
#taxa = tree.full_taxa_map()
#with open('full_taxa.pickle', 'wb') as handle:
#    pickle.dump(taxa, handle)
taxa = None
with open('full_taxa.pickle', 'rb') as handle:
    taxa = pickle.load(handle)

start_time2 = time.time()
#print (len(taxa['phylum']))
#print (len(taxa['class']))
#print (len(taxa['order']))
#print (len(taxa['family']))
#print ([len(v) for x,v in taxa().items()])


def proc_simple_data(data, sd):
    global tree, taxa
    import decimal
    from apps.data.models import Taxon
    from bs4 import BeautifulSoup

    # higher taxa
    #print (tree.rank_map.split('|')[:-2])
    for rank in tree.rank_map.split('|')[:-2]:
        taxon_field = rank
        if rank == 'class':
            taxon_field = 'class_field'
        try:
            #print (rank, data[taxon_field], taxa[rank][data[taxon_field]])
            setattr(sd, 'taxon_{}_id'.format(rank), taxa[rank][data[taxon_field]])
        except Exception as e:
            pass
            #print ('err', e)

    # species
    try:
        scname = data['scientificname']
        sd.scientific_name = scname
        species_id, genus_id = taxa['sci_name'][scname] 
        #print (species_id, genus_id, 'xx')
        sd.taxon_genus_id = genus_id
        sd.taxon_species_id = species_id
        # data.specificEpithet:
    except:
        pass

    try:
        sd.year = int(float(data['year']))
    except:
        sd.year = None

    try:
        sd.month = int(float(data['month']))
    except:
        sd.month = None

    try:
        sd.day = int(float(data['day']))
    except:
        sd.day = None

    try:
        sd.country = data['country']
    except:
        sd.country = None

    try:
        sd.longitude = decimal.Decimal(data['decimallongitude'])
        if len(data['decimallongitude'].split('.')[0]) >= 3:
            raise
    except:
        sd.longitude = None


    try:
        if len(data['decimallatitude'].split('.')[0]) >= 3:
            # 有 longitude 跟 latitude 寫反, 又剛好 120.0 > save 後會變成 120.00000000 (超過 max_digits=10)
            raise
        sd.latitude = decimal.Decimal(data['decimallatitude'])
    except:
        sd.latitude = None

    err = {}

    return sd, err

# chunkzie or process will be killed in docker
for i in range(chunk_num_begin, chunk_num):
    begin = 0 if i == 0 else i*chunk_size
    end = (i+1)*chunk_size
    #print (all_data[begin:end])

    #begin = 482990
    #end = 500000
    print ('begin', begin, end)
    for data in all_data[begin:end]:
        sd = SimpleData(taibif_id=data['taibif_id'], taibif_dataset_name=data['taibif_dataset_name'])
        sd_ret, err = proc_simple_data(data, sd)
        try:
            sd_ret.save()
        except Exception as e:
            sd.save()
            print ('save', data['taibif_id'], e)

    end_time = time.time()
    print ('time:', end, start_time2 - start_time, end_time-start_time2)



'''rows = []
for i in rows:
    sd = SimpleData(taibif_id=i)
    sd.save()
    if i.kingdom:
        t = _get_taxon('kingdom', i.kingdom)
        if t:
            sd.taxon_kingdom = t
    if i.phylum:
        t = _get_taxon('phylum', i.phylum)
        if t:
            sd.taxon_phylum = t
    if i.class_field:
        t = _get_taxon('class', i.class_field)
        if t:
            sd.taxon_class = t
    if i.order:
        t = _get_taxon('order', i.order)
        if t:
            sd.taxon_order = t
    if i.family:
        t = _get_taxon('family', i.family)
        if t:
            sd.taxon_family = t
    if i.genus:
        t = _get_taxon('genus', i.genus)
        if t:
            sd.taxon_genus = t
    if i.scientificname or i.specificepithet:
        if i.specificepithet:
            t = Taxon.objects.filter(rank='species', name=i.specificepithet).first()
        if t:
            sd.taxon_species = t
        elif i.scientificname:
            sc_list = i.scientificname.split(' ')
            if len(sc_list) > 1:
                t = Taxon.objects.filter(rank='species', name=sc_list[1]).first()
                if t:
                    sd.taxon_species = t

    #if i.decimallongitude:
    if i.year:
        try:
            sd.year = int(i.year)
        except:
            print ('err-year:', i.taibif_id, i.year)
    if i.month:
        try:
            sd.month = int(i.month)
        except:
            print ('err-month:', i.taibif_id, i.month)

    if i.day:
        try:
            sd.day = int(i.day)
        except:
            print ('err-day:', i.taibif_id, i.day)

    if i.decimallongitude:
        try:
            sd.longitude = float(i.decimallongitude)
        except:
            print ('err-lng:', i.taibif_id, i.decimallongitude)
    if i.decimallatitude:
        try:
            sd.latitude = float(i.decimallatitude)
        except:
            print ('err-lat:', i.taibif_id, i.decimallatitude)

    if i.taibif_id % 100000 == 0:
        print ('count', i.taibif_id, time.time()-start)

    try:
        sd.save()
    except:
        print ('error', i.taibif_id)'''
