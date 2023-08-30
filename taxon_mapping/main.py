import os
import datetime
import pandas as pd
import sqlalchemy as db
import requests
import json
from pandarallel import pandarallel
import multiprocessing
from datetime import date



# Update TaiCOL Taxon [Basic] Information
def update_taicol_taxon(row):
    taicol_taxon_url = 'https://api.taicol.tw/v2/taxon?taxon_id='+str(row['taicol_taxon_id'])
    taxon_resp = requests.get(taicol_taxon_url , json={"test" : "in"})
    data = json.loads(taxon_resp.content.decode('utf-8'))
    
    try:
        # 有正常回應，可接受，且有結果大於一筆
        if (taxon_resp.status_code == 200) and (data.get('data')) and (len(data['data']) > 0):
            is_accepted_name = False
            if data['data'][0]['status'] == 'Accepted':
                is_accepted_name = True
            row['rank'] = data['data'][0]['rank']
            row['is_accepted_name'] = is_accepted_name
            row['taicol_name_id'] = data['data'][0]['name_id']
            row['name'] = data['data'][0]['simple_name']
            row['name_author'] = data['data'][0]['name_author']
            row['formatted_name'] = data['data'][0]['formatted_name']
            row['taicol_synonyms'] = data['data'][0]['synonyms']
            row['formatted_synonyms'] = data['data'][0]['formatted_synonyms']
            row['misapplied'] = data['data'][0]['misapplied']
            row['formatted_misapplied'] = data['data'][0]['formatted_misapplied']
            row['rank'] = data['data'][0]['rank']
            row['name_zh'] = data['data'][0]['common_name_c']
            row['alternative_name_c'] = data['data'][0]['alternative_name_c']
            row['is_hybrid'] = data['data'][0]['is_hybrid']
            row['is_endemic'] = data['data'][0]['is_endemic']
            row['is_in_taiwan'] = data['data'][0]['is_in_taiwan']
            row['alien_type'] = data['data'][0]['alien_type']
            row['is_fossil'] = data['data'][0]['is_fossil']
            row['is_terrestrial'] = data['data'][0]['is_terrestrial']
            row['is_freshwater'] = data['data'][0]['is_freshwater']
            row['is_brackish'] = data['data'][0]['is_brackish']
            row['is_marine'] = data['data'][0]['is_marine']
            row['cites'] = data['data'][0]['cites']
            row['iucn'] = data['data'][0]['iucn']
            row['redlist'] = data['data'][0]['redlist']
            row['protected'] = data['data'][0]['protected']
            row['sensitive'] = data['data'][0]['sensitive']
            row['updated_at'] = data['data'][0]['updated_at']
            row['new_taxon_id'] = data['data'][0]['new_taxon_id']
            
    except Exception as e :
        row['mapping_error'] = "taxon api error == " + e
        
    return pd.Series(row) 


# Update TaiCOL Taxon [name_author/protologue] Information
def update_name_api(row):
    taicol_name_url = 'https://api.taicol.tw/v2/name?name_id='+str(row['taicol_name_id'])
    name_resp = requests.get(taicol_name_url , json={"test" : "in"})
    data = json.loads(name_resp.content.decode('utf-8'))
    
    try:
        # 有正常回應，且有結果
        if (name_resp.status_code == 200) and (data.get('data')) and (len(data['data']) > 0):
            row['name_author'] = data['data'][0]['name_author']
            row['reference'] = data['data'][0]['protologue']
    
    except Exception as e :
        if row['mapping_error']:
            row['mapping_error'] = str(row['mapping_error'])  if row['mapping_error']  != None else '' + ". Name api error == " + e
        else:
            row['mapping_error'] = "name api error == " + e
        
    return pd.Series(row) 


# Update TaiCOL [path] Information
def update_highertaxon_api(row):
    taicol_highertaxon_url = 'https://api.taicol.tw/v2/higherTaxa?taxon_id='+str(row['taicol_taxon_id'])
    highertaxon_resp = requests.get(taicol_highertaxon_url , json={"test" : "in"})
    data = json.loads(highertaxon_resp.content.decode('utf-8'))
    
    # 有正常回應，且有結果
    higher_taxon = []
    try: 
        if (highertaxon_resp.status_code == 200) and (data.get('data')) and (len(data['data']) > 0):
            for i in data['data']:
                if i['taxon_id'] != None:
                    higher_taxon.append(i['taxon_id'])
                else:
                    un_name = i['simple_name']
                    # a = f"SELECT * FROM data_taxon WHERE name='{un_name}'"
                    # 確認 地位未定 是否有存入
                    un_id = pd.read_sql(f"SELECT * FROM data_taxon WHERE name='{un_name}'", connection)
                    if not un_id.empty:
                        higher_taxon.append(un_id['taicol_taxon_id'])
                    else:
                        # 建立新的 不確定值 IS:incertae sedis
                        max_is = pd.read_sql("SELECT * FROM data_taxon WHERE taicol_taxon_id like 'IS-%%' ORDER BY id DESC limit 1", connection)
                        max_id = pd.read_sql("SELECT * FROM data_taxon ORDER BY id DESC limit 1", connection)
                        
                        if not max_is.empty:
                            num = 'IS-'+'{0:06d}'.format(int(str(max_is['taicol_taxon_id'][0]).split('-',1)[1]) + 1)
                        else:
                            num = 'IS-000001'
                        higher_taxon.append(num)
                        tmp_parent = i['simple_name'].split(' ',1)[0]
                        tmp_parent_id = pd.read_sql(f"SELECT * FROM data_taxon WHERE name like '{tmp_parent}' ORDER BY id DESC limit 1", connection)
                        new_is = [{
                            'id':int(max_id['id'])+1,
                            'taicol_taxon_id':num,
                            'name':i['simple_name'],
                            'formatted_name':i['formatted_name'],
                            'name_zh':i['common_name_c'],
                            'rank':i['rank'],
                            'updated_at':datetime.datetime.now(),
                            'is_accepted_name':False,
                            'parent_id':int(tmp_parent_id['id']),
                            'is_brackish':False,
                            'is_endemic':False,
                            'is_fossil':False,
                            'is_freshwater':False,
                            'is_terrestrial':False,
                            'is_hybrid':False,
                            'is_in_taiwan':True,
                            'is_marine':False,
                        }]
                        
                        tmp = pd.DataFrame.from_dict(new_is,orient='columns')
                        # 加入  simple_name ,formatted_name , rank,common_name_c : IS-000001
                        # test.to_sql('temp_taxon', engine, if_exists='append',index=False)
                        tmp.to_sql('data_taxon', engine, if_exists='append',index=False)
            tmp_parent_name = data['data'][1]['simple_name']
            tmp_parent_id = pd.read_sql(f"SELECT * FROM data_taxon WHERE name like '{tmp_parent_name}' ORDER BY id DESC limit 1", connection)
            row['parent_id'] = int(tmp_parent_id['id'])
                        
        if len(data['data']) > 1:
            row['parent_taxon_id'] = data['data'][1]['taxon_id']
            

        if len(higher_taxon)>0:
            try:
                row['path'] = '>'.join(higher_taxon)
            except Exception as e:
                print(higher_taxon)
                print(e)

    except Exception as e:
        print("!!! Exception === !!! ",e )
        print()
        if row['mapping_error']:
            row['mapping_error'] = str(row['mapping_error'])  if row['mapping_error']  != None else '' + ". highertaxon api error == " + e
        else:
            row['mapping_error'] = "highertaxon api error == " + str(e)
    return pd.Series(row) 


# 前置準備 - 建立 Postgres 資料庫於本地端，目前設置port為 9432

# 1. 原本 TaiCOL 更新
# 2. 新 TaiCOL 加入

print("==== STEP 0 = Load Database Information ====")

engine = db.create_engine('postgresql://postgres:example@127.0.0.1:9432/taibif') 
connection = engine.connect()
df_taxon = pd.read_sql('SELECT * FROM data_taxon', connection)

# ---- update Taxon information 
sql_delete_temp_taxon =  "DELETE FROM temp_taxon"
with engine.begin() as conn:    
    conn.execute(sql_delete_temp_taxon)

df_taxon['mapping_error'] = ''
df_taicolid_notnull = df_taxon[df_taxon.taicol_taxon_id.notnull()]

today = date.today().strftime('%Y%m%d')

print("START TIME === " ,datetime.datetime.now())
print("START DATE === " ,today )
print("==== STEP 1 = Update TaiCOL Taxon Information ====")

# 1. 資料庫 資料 更新

# 單筆執行
print("==== update_taicol_taxon === ")
df_taicolid_notnull  = df_taicolid_notnull.apply(update_taicol_taxon, axis=1)
print("==== update_name_api === ")
df_taicolid_notnull  = df_taicolid_notnull.apply(update_name_api, axis=1)
print("==== update_highertaxon_api === ")
df_taicolid_notnull  = df_taicolid_notnull.apply(update_highertaxon_api, axis=1)
df_taicolid_notnull.to_sql('temp_taxon', engine, if_exists='append',index=False)
output_path=f'./results/update_taicol_taxon_{today}.csv'
df_taicolid_notnull.to_csv(output_path, mode='a', header=not os.path.exists(output_path))

# 分散執行
# n=4000
# print("==== update_taicol_taxon === ")
# list_df = [df_taicolid_notnull[i:i+n] for i in range(0,len(df_taicolid_notnull),n)]
# for idx, x in enumerate(list_df):
#     pandarallel.initialize(progress_bar=True)
#     list_df[idx] = list_df[idx].parallel_apply(update_taicol_taxon,axis=1)

# print("==== update_name_api === ")
# for idx, x in enumerate(list_df):
#     pandarallel.initialize(progress_bar=True)
#     list_df[idx] = list_df[idx].parallel_apply(update_name_api,axis=1)

# print("==== update_highertaxon_api === ")
# for idx, x in enumerate(list_df):
#     pandarallel.initialize(progress_bar=True)
#     list_df[idx] = list_df[idx].parallel_apply(update_highertaxon_api,axis=1)
    
#     list_df[idx].to_sql('temp_taxon', engine, if_exists='append',index=False)
#     output_path=f'./results/update_taicol_taxon_{today}.csv'

#     list_df[idx].to_csv(output_path, mode='a', header=not os.path.exists(output_path))


print("==== STEP 2 = New TaiCOL Taxon ID ====")
# 2. 新 TaiCOL 資料 加入
new_taxon = pd.read_sql('SELECT * FROM temp_taxon WHERE new_taxon_id IS NOT NULL', connection)

# original function
new_taxon  = new_taxon.apply(update_taicol_taxon, axis=1)
# new_taxon.to_csv(f'./taxon_mapping/results/update_taicol_new_taxon_{today}.csv')

n=4000
list_df = [new_taxon[i:i+n] for i in range(0,len(new_taxon),n)]
print("==== update_taicol_taxon === ")
for idx, x in enumerate(list_df):
    pandarallel.initialize(progress_bar=True)
    list_df[idx] = list_df[idx].parallel_apply(update_taicol_taxon,axis=1)

print("==== update_name_api === ")
for idx, x in enumerate(list_df):
    pandarallel.initialize(progress_bar=True)
    list_df[idx] = list_df[idx].parallel_apply(update_name_api,axis=1)

print("==== update_highertaxon_api === ")
for idx, x in enumerate(list_df):    
    pandarallel.initialize(progress_bar=True)
    list_df[idx] = list_df[idx].parallel_apply(update_highertaxon_api,axis=1)

    list_df[idx].to_sql('temp_taxon', engine, if_exists='append',index=False)

    output_path=f'./taxon_mapping/results/update_taicol_new_taxon_{today}.csv'
    list_df[idx].to_csv(output_path, mode='a', header=not os.path.exists(output_path))

# ---- update Taxon information 

sql_taxon = """ UPDATE data_taxon AS dt
SET rank=tt.rank,name=tt.name,name_zh=tt.name_zh,count=tt.count,parent_id=tt.parent_id,is_accepted_name=tt.is_accepted_name,source_id=tt.source_id,taieol_desc=tt.taieol_desc,taieol_pic=tt.taieol_pic,reference=tt.reference,class_id=tt.class_id,family_id=tt.family_id,genus_id=tt.genus_id,kingdom_id=tt.kingdom_id,order_id=tt.order_id,phylum_id=tt.phylum_id,accepted_name_id=tt.accepted_name_id,backbone=tt.backbone,taicol_name_id=tt.taicol_name_id,taicol_taxon_id=tt.taicol_taxon_id,class_taxon_id=tt.class_taxon_id,family_taxon_id=tt.family_taxon_id,formatted_name=tt.formatted_name,genus_taxon_id=tt.genus_taxon_id,kingdom_taxon_id=tt.kingdom_taxon_id,name_author=tt.name_author,order_taxon_id=tt.order_taxon_id,phylum_taxon_id=tt.phylum_taxon_id,parent_taxon_id=tt.parent_taxon_id,path=tt.path,alien_type=tt.alien_type,alternative_name_c=tt.alternative_name_c,cites=tt.cites,formatted_misapplied=tt.formatted_misapplied,formatted_synonyms=tt.formatted_synonyms,is_brackish=tt.is_brackish,is_endemic=tt.is_endemic,is_fossil=tt.is_fossil,is_freshwater=tt.is_freshwater,is_hybrid=tt.is_hybrid,is_in_taiwan=tt.is_in_taiwan,is_marine=tt.is_marine,is_terrestrial=tt.is_terrestrial,iucn=tt.iucn,misapplied=tt.misapplied,new_taxon_id=tt.new_taxon_id,protected=tt.protected,redlist=tt.redlist,sensitive=tt.sensitive,updated_at=tt.updated_at
FROM temp_taxon AS tt
WHERE dt.id = tt.id
""" 

with engine.begin() as conn:
    conn.execute(sql_taxon)
    
print("END TIME === " ,datetime.datetime.now())
