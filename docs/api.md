# TaiBIF API

API基礎網址為
https://portal.taibif.tw/api/

## 出現紀錄 OCCURRENCE

### 出現紀錄查詢 Occurrence search
----
取得出現紀錄詳細資料，包含原始資料及詮釋資料。

|Resource URL|請求方式 (Method)|回應資訊(Response) |  資料描述(Description) | 呼叫參數(Parameters)|
| -------- | -------- | -------- | -------- | -------- | 
|/v2/occurrence/search|GET|Occurrence|取得出現紀錄的詳細資訊，包含原始及詮釋資料。|q,habitat,scientificNameID,references,year,individualCount,county,fieldNumber,decimalLatitude,type,geom,class_zh,locationAccordingTo,occurrenceStatus,taibif_dataset_name_zh,id,verbatimElevation,family_zh,level_0,order,infraspecificEpithet,phylum_zh,organismQuantity,verbatimEventDate,georeferencedBy,endDayOfYear,locality,minimumElevationInMeters,index,collectionCode,materialSampleID,occurrenceID,order_zh,verbatimLatitude,taibif_county,genus,organismQuantityType,acceptedNameUsageID,ownerInstitutionCode,higherClassification,continent,order_key,latitude,minimumDepthInMeters,higherGeographyID,phylum_key,locationRemarks,taibif_dataset_name,countryCode,kingdom_key,verbatimLongitude,rights,eventTime,nameAccordingTo,behavior,identifiedBy,nomenclaturalCode,georeferenceProtocol,sex,class_key,associatedMedia,waterBody,disposition,otherCatalogNumbers,lifeStage,locationID,verbatimCoordinates,startDayOfYear,verbatimTaxonRank,georeferenceSources,rightsHolder,country,institutionID,scientificName,grid_x,municipality,associatedReferences,language,establishmentMeans,taxonRemarks,catalogNumber,basisOfRecord,fieldNotes,organismName,modified,maximumDepthInMeters,day,reproductiveCondition,recordNumber,georeferencedDate,acceptedNameUsage,family_key,higherGeography,island,georeferenceRemarks,decimalLongitude,stateProvince,verbatimLocality,maximumElevationInMeters,license,month,organismID,dateIdentified,kingdom_zh,publisher,samplingProtocol,coreid,collectionID,eventDate,name_zh,eventID,scientificNameAuthorship,coordinateUncertaintyInMeters,associatedTaxa,longtitude,taxonRank,eventRemarks,identificationVerificationStatus,taxonID,preparations,vernacularName,institutionCode,genus_zh,namePublishedIn,identificationRemarks,class,informationWithheld,dataGeneralizations,species_key,georeferenceVerificationStatus,typeStatus,verbatimSRS,datasetName,verbatimCoordinateSystem,geodeticDatum,kingdom,verbatimDepth,specificEpithet,recordedBy,phylum,_version_,previousIdentifications,coordinatePrecision,originalNameUsage,taibif_occ_id,taxon_backbone,datasetID,occurrenceRemarks,grid_y,genus_key,associatedSequences,family,facet|

**參數**


| 參數名稱 |  參數描述 |查詢範例|
| -------- | -------- | --------  |
| q | 關鍵字查詢 |/api/v2/occurrence/search?q=olypedates braueri|
|year| 年份搜尋，採範圍搜尋| /api/v2/occurrence/search?year=2000,2010|
|country|國家|/api/v2/occurrence/search?country=Taiwan|
|dataset|資料集|/api/v2/occurrence/search?dataset=Taiwan Wild Bird Federation Bird Records Database&dataset|
|month|月份|/api/v2/occurrence/search?month=2&month=9|
|publisher|資料集發布者|/api/v2/occurrence/search?publisher=|
|taibif_county|台灣縣市|/api/v2/occurrence/search?taibif_county=22|
|facet|參數總計|/api/v2/occurrence/search?facet=year&facet=month&facet=dataset&facet=publisher&facet=country|
|rows|詳細資料回傳筆數|/api/v2/occurrence/search?rows=1|
|debug_solr|除錯資訊|debug_solr=1|




### 出現紀錄指標 Occurrence  Chart
----
出現紀錄指標，取得指標所需的統計值

|Resource URL|請求方式 (Method)|回應資訊(Response) |  資料描述(Description) | 呼叫參數(Parameters)|
| -------- | -------- | -------- | -------- | -------- |
|/v1/occurrence/charts|GET|Occurrence|取得各項參數的總計| dataset, year, month |

**參數**

| 參數名稱 |  參數描述 |查詢範例|
| -------- | -------- | --------  |
|month|月份|/api/v1/occurrence/charts?month=1&month=3|
|dataset|資料集|/api/v1/occurrence/charts?dataset=Taiwan Wild Bird Federation Bird Records Database&dataset=Reef Check in Taiwan 台灣珊瑚礁體檢&dataset=The Taiwan Roadkill Observation Network Data Set.|
|year|年份|/api/v1/occurrence/charts?month=3&year=2018,2021|


## 資料集 DATASET

## 物種 TAXON

## 發布單位 ORGANIZATION