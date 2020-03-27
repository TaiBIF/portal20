from apps.sdata.models import (
    Dataset,
    DatasetOrganization,
    Taxon,
    RawDataOccurrence
)

class SuperSearch(object):

    def __init__(self):
        pass

class OccurrenceSearch(SuperSearch):

    offset = 20
    limit = -1
    query = RowDataOccurrence.objects

    def __init__(self):
        pass
        #super().__init__()


    def_
