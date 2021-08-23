from django.db.models import (
    Count,
    Sum,
)
from apps.data.models import (
    Dataset,
    #SimpleData,
)
from utils.general import get_cache_or_set

def _get_home_stats():
    dataset_stats = Dataset.public_objects.aggregate(num_occur=Sum('num_occurrence'), num_dataset=Count('name'))
    #species_count = SimpleData.public_objects.values('scientific_name').annotate(total=Count('scientific_name')).count()
    #a = SimpleData.public_objects.aggregate(total=Count('scientific_name')) # 4456372 ? why?
    species_count = 0
    stats = {
        'num_occurrence': dataset_stats['num_occur'],
        'num_dataset': dataset_stats['num_dataset'],
        'num_species': species_count, # TODO
    }
    return stats

def get_home_stats():
    return get_cache_or_set('home_stats', _get_home_stats)
