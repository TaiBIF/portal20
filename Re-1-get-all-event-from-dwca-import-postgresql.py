#!/usr/bin/env python
# coding: utf-8

# In[1]:


columns = [
    'eventID',
    'eventRemarks', 
    'eventStatus',    
    'institutionID', 
    'institutionCode',
    'ownerInstitutionCode',
    'collectionID', 
    'collectionCode',
    'catalogNumber', 
    'otherCatalogNumbers',    
    'recordNumber',
    'recordedBy',
    'fieldNumber',
    'fieldNotes',    
    'basisOfRecord',    
    'datasetID',  
    'datasetName', 
    'language', 
    'type',
    'typeStatus',    
    'coreid',
    'lifeStage',
    'eventTime',
    'eventRemarks',
    'year',    
    'month',
    'day',     
    'startDayOfYear',
    'endDayOfYear',    
    'eventDate',    
    'eventID', 
    'verbatimEventDate',
    'verbatimDepth',
    'kingdom', 
    'phylum', 
    'class',    
    'order',    
    'family',    
    'genus', 
    'subgenus',
    'vernacularName',  
    'scientificName',
    'scientificNameID',     
    'taxonRank',
    'taxonID',    
    'verbatimTaxonRank',
    'associatedTaxa',
    'specificEpithet',      
    'scientificNameAuthorship',
    'acceptedNameUsage',
    'acceptedNameUsageID',
    'originalNameUsage',
    'nameAccordingTo',
    'higherClassification',
    'taxonRemarks',
    'dateIdentified',    
    'identificationQualifier',
    'identifiedBy',
    'identificationVerificationStatus',
    'previousIdentifications',
    'county', 
    'country',    
    'countryCode',
    'stateProvince',
    'locality',    
    'locationID',
    'higherGeography',     
    'georeferencedDate',
    'georeferenceSources',
    'georeferencedBy',  
    'geodeticDatum', 
    'georeferenceProtocol',
    'georeferenceRemarks',   
    'georeferenceVerificationStatus',
    'decimalLongitude', 
    'decimalLatitude',    
    'verbatimLatitude', 
    'verbatimLongitude',    
    'verbatimLocality',    
    'verbatimCoordinates',
    'coordinateUncertaintyInMeters',    
    'verbatimCoordinateSystem',    
    'coordinatePrecision', 
    'locationAccordingTo',
    'pointRadiusSpatialFit', 
    'rights',
    'rightsHolder',   
    'license',     
    'preparations',    
    'id',     
    'modified', 
    'dataGeneralizations',  
    'organismID',    
    'organismQuantityType',
    'organismQuantity',    
    'sex',    
    'individualCount', 
    'verbatimElevation',
    'minimumElevationInMeters',
    'maximumElevationInMeters',    
    'minimumDepthInMeters', 
    'maximumDepthInMeters',    
    'waterBody',
    'island',    
    'habitat',
    'reproductiveCondition',
    'continent',
    'infraspecificEpithet',
    'footprintWKT',
    'associatedMedia',
    'associatedSequences', 
    'associatedReferences',    
    'nomenclaturalCode',
    'footprintSpatialFit',
    'establishmentMeans',    
    'behavior', 
    'informationWithheld', 
    'islandGroup',
    'municipality', 
    'materialSampleID',    
    'samplingProtocol',
    'samplingEffort',    
    'disposition',
    'references',
    'namePublishedInYear', 
    'namePublishedIn',
    'dataset_name',
    'q_year',
    'q_month',
    'q_day'
]

# via: https://github.com/tdwg/dwc/tree/master/dist
dwc_terms_str = 'type,modified,language,license,rightsHolder,accessRights,bibliographicCitation,references,institutionID,collectionID,datasetID,institutionCode,collectionCode,datasetName,ownerInstitutionCode,basisOfRecord,informationWithheld,dataGeneralizations,dynamicProperties,occurrenceID,catalogNumber,recordNumber,recordedBy,individualCount,organismQuantity,organismQuantityType,sex,lifeStage,reproductiveCondition,behavior,establishmentMeans,occurrenceStatus,preparations,disposition,associatedMedia,associatedReferences,associatedSequences,associatedTaxa,otherCatalogNumbers,occurrenceRemarks,organismID,organismName,organismScope,associatedOccurrences,associatedOrganisms,previousIdentifications,organismRemarks,materialSampleID,eventID,parentEventID,fieldNumber,eventDate,eventTime,startDayOfYear,endDayOfYear,year,month,day,verbatimEventDate,habitat,samplingProtocol,sampleSizeValue,sampleSizeUnit,samplingEffort,fieldNotes,eventRemarks,locationID,higherGeographyID,higherGeography,continent,waterBody,islandGroup,island,country,countryCode,stateProvince,county,municipality,locality,verbatimLocality,minimumElevationInMeters,maximumElevationInMeters,verbatimElevation,minimumDepthInMeters,maximumDepthInMeters,verbatimDepth,minimumDistanceAboveSurfaceInMeters,maximumDistanceAboveSurfaceInMeters,locationAccordingTo,locationRemarks,decimalLatitude,decimalLongitude,geodeticDatum,coordinateUncertaintyInMeters,coordinatePrecision,pointRadiusSpatialFit,verbatimCoordinates,verbatimLatitude,verbatimLongitude,verbatimCoordinateSystem,verbatimSRS,footprintWKT,footprintSRS,footprintSpatialFit,georeferencedBy,georeferencedDate,georeferenceProtocol,georeferenceSources,georeferenceVerificationStatus,georeferenceRemarks,geologicalContextID,earliestEonOrLowestEonothem,latestEonOrHighestEonothem,earliestEraOrLowestErathem,latestEraOrHighestErathem,earliestPeriodOrLowestSystem,latestPeriodOrHighestSystem,earliestEpochOrLowestSeries,latestEpochOrHighestSeries,earliestAgeOrLowestStage,latestAgeOrHighestStage,lowestBiostratigraphicZone,highestBiostratigraphicZone,lithostratigraphicTerms,group,formation,member,bed,identificationID,identificationQualifier,typeStatus,identifiedBy,dateIdentified,identificationReferences,identificationVerificationStatus,identificationRemarks,taxonID,scientificNameID,acceptedNameUsageID,parentNameUsageID,originalNameUsageID,nameAccordingToID,namePublishedInID,taxonConceptID,scientificName,acceptedNameUsage,parentNameUsage,originalNameUsage,nameAccordingTo,namePublishedIn,namePublishedInYear,higherClassification,kingdom,phylum,class,order,family,genus,subgenus,specificEpithet,infraspecificEpithet,taxonRank,verbatimTaxonRank,scientificNameAuthorship,vernacularName,nomenclaturalCode,taxonomicStatus,nomenclaturalStatus,taxonRemarks'


import os
import re

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from dwca.read import DwCAReader


# In[2]:


IPT_DWCA_PATH = 'ipt-dwca'
counter = 0
dwc_terms_list = dwc_terms_str.split(',')

# check all columns which not in dawrincore terms
for i in columns:
    if i not in dwc_terms_list:
        print ('[{}] not dw-c terms'.format(i))


# In[3]:


# change dwc-terms to lower and underline
def to_lower(name):
    # https://stackoverflow.com/a/7322163/644070
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
column_name_map = {}
for col in columns:
    if col == 'index':
        column_name_map[col] = 'id'
    elif col in ['type', 'class', 'order', 'id', 'license']:
        column_name_map[col] = '{}_field'.format(col)
    else:
        column_name_map[col] = to_lower(col)


# In[4]:


df_datasets = pd.read_csv('0-dataset-list_20200612-155723.csv')


# In[5]:


all_event = 0


# In[6]:


core_append = []
for i in df_datasets.iterrows():
    counter += 1
    r = i[1]['name'].replace('http://ipt.taibif.tw/eml.do?r=', '')
    fpath = os.path.join(IPT_DWCA_PATH, r) + '.zip'
    num_err = 0
    if os.path.exists(fpath):
        with DwCAReader(fpath) as dwca:
            #print (dwca.metadata)
            print (counter, i[1]['title'], dwca.descriptor.core.type,len(dwca.rows))
            if 'Event' in dwca.descriptor.core.type:
                #print (type(dwca.rows), '||')
                all_event += len(dwca.rows)
                core_df = dwca.pd_read('event.txt', parse_dates=True)
                
                #core_append.append(core_df)
                
                if 'year' in core_df.columns.to_list():
                    idx = 0
                    for x in core_df.iterrows():
                        core_df.at[idx, 'q_year'] = x[1]['year']
                        if 'month' in core_df.columns.to_list():
                            core_df.at[idx, 'q_month'] = x[1]['month']
                        if 'day' in core_df.columns.to_list():
                            core_df.at[idx, 'q_day'] = x[1]['day']
                        idx += 1
                #core_df['index'] = counter
                df_all_event = pd.DataFrame(columns=list(core_df.columns))
                core_append.append(core_df)
                res_f = pd.concat(core_append, ignore_index=True, sort=False) 
                df_all_event = pd.concat([df_all_event, res_f],sort=False,ignore_index=True) ##Get the occurrence ID and other infor.
                
                #core_df.rename(columns=column_name_map)
                #core_df.to_sql('data_occurrence', engine, index_label='id', if_exists='append')
                #print (core_df)
                
            else:
                extensions = dwca.descriptor.extensions_type
                if 'http://rs.tdwg.org/dwc/terms/Event' in extensions:
                    ext_df = dwca.pd_read('event.txt')
                    ext_df['dataset_name'] = dataset_name
                    #ext_df['index'] = counter
                    #edf.columns = [column_name_map[x] for x in edf.columns]
                    
                    ## add event column if Event!
                    ''''if 'Event' in dwca.descriptor.core.type:
                        event_df = dwca.pd_read('event.txt')
                        has_event_date = False
                        if 'eventDate' in event_df.columns.to_list():
                            event_df = dwca.pd_read('event.txt', parse_dates=['eventDate'])
                            has_event_date = True
                            
                        idx = 0
                        for o in ext_df.iterrows():
                            event_id = o[1]['eventID']
                            e = event_df.loc[event_df['eventID']==event_id]
                            for t in event_df.columns.to_list():
                                if not e.empty:
                                    s = e.iloc[0][t]
                                    if has_event_date and t == 'eventDate':
                                        s = s.strftime('%Y-%m-%d')
                                        #print (s, type(s))
                                    try:
                                        ext_df.at[idx, t] = s
                                    except:
                                        num_err += 1
                                        #print (type(s), s)
                            idx += 1'''
                        
                        
                    all_event += len(ext_df)
                    #print (edf.columns)
                    df_all_event = pd.concat([df_all_event, ext_df],sort=False,ignore_index=True)
                    #ext_df.rename(columns=column_name_map)
                    #ext_df.to_sql('data_occurrence', engine, index_label='id', if_exists='append')
                
                
              


# In[7]:


df_all_event


# In[8]:


from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:jonghoonharuma@localhost:5432/test')


# In[9]:


df_all_event.to_sql('event_20200618', engine)


# In[176]:


df_all_event.to_csv('out_all_event_copy.csv',encoding="utf_8_sig")
#display(df_all_occur)
#print (df_all_occur.columns)
df_all_event = df_all_event.rename(columns=column_name_map)
#print (df_all_occur.columns)               

            
                


# In[ ]:





# In[ ]:




