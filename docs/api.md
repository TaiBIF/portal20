# TaiBIF API

## Occurrence search

get occurrence records


/api/v2/occurrence/search



**parameters**


q, dataset, year, month, publisher => filter


facet=dataset,year,month,publisher,country => enable facet

debug_solr=1 => show debug info

**examples**

```
/api/v2/occurrence/search?q=olypedates braueri
/api/v2/occurrence/search?year=2000,2010
/api/v2/occurrence/search?country=Taiwan&dataset=taif&facet=year&facet=month&facet=dataset&facet=publisher&facet=country

/api/v2/occurrence/search?country=Malaysia&month=2&month=9&facet=year&facet=month&facet=dataset&facet=publisher&facet=country&debug_solr=1
results: 32 (month=2 => 30, month=9 => 2)

```

## Occurrence Chart

get occurrence records

### Search

/api/v1/occurrence/charts

**parameters**


dataset, year, month


facet=dataset,year,month

**examples**

```
/api/v1/occurrence/charts?month=1
month=1, 9749
/api/v1/occurrence/charts?month=3
month=3, 10379
/api/v1/occurrence/charts?month=1&month=3

/api/v1/occurrence/charts?month=3&year=2018,2021
year=2018,166 ; year=2019,6 ; month=3, 172

/api/v1/occurrence/charts?year=2018,2021
year=2018,60717 ; year=2019,42
/api/v1/occurrence/charts?year=2015,2017
year=2017,78455 ; year=2016,69502 ; year=2015:62941
/api/v1/occurrence/charts?year=2015,2021

/api/v1/occurrence/charts?dataset=Taiwan Wild Bird Federation Bird Records Database&month=1
/api/v1/occurrence/charts?year=2018,2021&dataset=Taiwan Wild Bird Federation Bird Records Database
year=0,dataset=0

/api/v1/occurrence/charts?dataset=Taiwan Wild Bird Federation Bird Records Database&dataset=Reef Check in Taiwan 台灣珊瑚礁體檢&dataset=The Taiwan Roadkill Observation Network Data Set.

The Taiwan Roadkill Observation Network Data Set. =46416
Reef Check in Taiwan 台灣珊瑚礁體檢 =3369
Taiwan Wild Bird Federation Bird Records Database =1853589

/api/v1/occurrence/charts?year=2018,2021&dataset=Four Bird Species in Rice Paddies in Shen-Gou Village, Yilan
year=2018,293 ; Four Bird Species in Rice Paddies in Shen-Gou Village, Yilan = 293
```
