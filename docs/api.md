/# TaiBIF API

## Occurrence

get occurrence records

### Search

/api/v2/occurrence/search

**parameters**


q, dataset, year, month, publisher


facet=dataset,year,month,publisher,country

**examples**

```
/api/v2/occurrence/search?q=olypedates braueri
/api/v2/occurrence/search?year=2000,2010
/api/v2/occurrence/search?country=Taiwan&dataset=taif&facet=year&facet=month&facet=dataset&facet=publisher&facet=country

```
