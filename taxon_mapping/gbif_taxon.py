import pandas as pd
import sqlalchemy as db
import requests
import json
import datetime
from datetime import date

def update_namecode(row):
    gbif_url = 'http://127.0.0.1:8081/api.php?format=json&source=gbif_backbone_txn&best=yes&names=' + str(row['name'])

    # solr 呼叫 nomanmatch 查詢
    # gbif_response = requests.post(gbif_url, json={"test": "in"})
    # gbif_data = json.loads(gbif_response.content.decode('utf-8'))
    gbif_response = requests.get(gbif_url)
    gbif_data = gbif_response.json()

    try:
        if gbif_data['data'][0][0]['results'][0]['match_type'] == 'Full match':
            row['taibif_accepted_namecode'] = gbif_data['data'][0][0]['results'][0]['accepted_namecode']
            row['taibif_namecode'] = gbif_data['data'][0][0]['results'][0]['namecode']
    except:
        print(row)
    return pd.Series(row)


def check_namecode(row):
    taicol_url = 'http://127.0.0.1:8081/api.php?format=json&source=taicol&best=yes&names=' + str(row['nM_name'])
    # taicol_response = requests.post(taicol_url, json={"test": "in"})
    # taicol_data = json.loads(taicol_response.content.decode('utf-8'))
    taicol_response = requests.get(taicol_url)
    taicol_data = taicol_response.json()


    # taicol_data 無資料會報錯後去查詢GBIF
    try:
        if taicol_data['data'][0][0]['results'][0]['match_type'] == 'Full match':
            row['taxon_backbone'] = 'TaiCOL'
    except:
        
        gbif_url = 'http://127.0.0.1:8080/api.php?format=json&source=gbif_backbone_txn&best=yes&names='+str(row['nM_name'])
        # gbif_response = requests.post(gbif_url, json={"test": "in"})
        # gbif_data = json.loads(gbif_response.content.decode('utf-8'))
        
        gbif_response = requests.get(gbif_url)
        gbif_data = gbif_response.json()
        
        try:
            if gbif_data['data'][0][0]['results'][0]['match_type'] == 'Full match':
                row['taxon_backbone'] = 'GBIF'
                row['taibif_scientificname'] = gbif_data['data'][0][0]['results'][0]['matched']
                row['taibif_accepted_namecode'] = gbif_data['data'][0][0]['results'][0]['accepted_namecode']
                row['taibif_namecode'] = gbif_data['data'][0][0]['results'][0]['namecode']
                row['taibif_vernacular_name'] = gbif_data['data'][0][0]['results'][0]['common_name']
                row['kingdomzh'] = gbif_data['data'][0][0]['results'][0]['kingdom']
                row['phylumzh'] = gbif_data['data'][0][0]['results'][0]['phylum']
                row['classzh'] = gbif_data['data'][0][0]['results'][0]['class']
                row['orderzh'] = gbif_data['data'][0][0]['results'][0]['order']
                row['familyzh'] = gbif_data['data'][0][0]['results'][0]['family']
                row['genuszh'] = gbif_data['data'][0][0]['results'][0]['genus']
                row['taxon_rank'] = gbif_data['data'][0][0]['results'][0]['taxon_rank']
                row['name_status'] = gbif_data['data'][0][0]['results'][0]['name_status']
        except:
            print(str(row['nM_name']),' match none')
    return pd.Series(row)


today = date.today().strftime('%Y%m%d')

print("START TIME === " ,datetime.datetime.now())
print("START DATE === " ,today )


# Step 1 : 查詢出現紀錄(solr)所有學名
solr_url = 'http://127.0.0.1:8983/solr/taibif_occurrence/select?facet.field=taibif_scientificname&facet.limit=-1&facet.mincount=-1&facet=true&fl=taibif_scientificname&indent=true&q.op=OR&q=*%3A*&rows=0'

inp_post_response = requests.get(solr_url)
data = json.loads(inp_post_response.content.decode('utf-8'))
taibif_sn = data['facet_counts']['facet_fields']['taibif_scientificname']
solr_name = []
for i in taibif_sn:
    if str(type(i))  == "<class 'str'>":
        solr_name.append(i)

# 建立 學名 dataframe 
df = pd.DataFrame (solr_name, columns = ['nM_name'])
df['taxon_backbone'] = ''
df['taibif_accepted_namecode'] = ''
df['taibif_namecode'] = ''
df['taibif_scientificname'] = ''
df['taibif_vernacular_name'] = ''
df['kingdomzh'] = ''
df['phylumzh'] = ''
df['classzh'] = ''
df['orderzh'] = ''
df['familyzh'] = ''
df['genuszh'] = ''
df['taxon_rank'] = ''

# 比對 Taxon backbone
tmp_nomenMatch_result = df.apply(check_namecode, axis=1)

# 匯出不同backbone 檔案
taicol = tmp_nomenMatch_result[tmp_nomenMatch_result['taxon_backbone']!='GBIF']
taicol.to_csv(f'./taicol_taxon.csv')

gbif = tmp_nomenMatch_result[tmp_nomenMatch_result['taxon_backbone']=='GBIF']
gbif.to_csv(f'./gbif_taxon.csv')

# 匯出empty檔案
empty = tmp_nomenMatch_result[tmp_nomenMatch_result['taxon_backbone']=='']
empty.to_csv(f'./empty_taxon.csv')


# Step2 : distinct各階層學名，匯入到Taxon Table 當中
seperated_file = pd.read_csv('./gbif_taxon.csv')
kingdomzh = pd.DataFrame({'name': seperated_file['kingdomzh'].unique(),'rank':'Kingdom'})
phylumzh = pd.DataFrame({'name': seperated_file['phylumzh'].unique(),'rank':'Phylum'})
classzh = pd.DataFrame({'name': seperated_file['classzh'].unique(),'rank':'Class'})
orderzh = pd.DataFrame({'name': seperated_file['orderzh'].unique(),'rank':'Order'})
familyzh = pd.DataFrame({'name': seperated_file['familyzh'].unique(),'rank':'Family'})
genuszh = pd.DataFrame({'name': seperated_file['genuszh'].unique(),'rank':'Genus'})

# 'is_accepted_name':true,'backbone':'GBIF', 'taibif_accepted_namecode':'','taibif_namecode':''

taxon_file = pd.concat([kingdomzh, phylumzh, classzh, orderzh,familyzh,genuszh], ignore_index=True)
taxon_file['backbone'] = 'GBIF'
taxon_file['taibif_accepted_namecode'] = ''
taxon_file['taibif_namecode'] = ''

tmp_nomenMatch_result = taxon_file.apply(update_namecode, axis=1)

# 合併species 資訊
seperated_file = seperated_file.rename(columns={'taibif_scientificname':'name','taxon_backbone':'backbone','taxon_rank':'rank'})
seperated_file = seperated_file.drop(columns=['Unnamed: 0','nM_name','taibif_vernacular_name','kingdomzh','phylumzh','classzh','orderzh','familyzh','genuszh'])
# print('seperated_file == ',seperated_file)

taxon_file_final = pd.concat([seperated_file,taxon_file], ignore_index=True)
# 所需要的欄位 id,rank,name,is_accepted_name,,backbone
taxon_file_final['is_accepted_name'] = 'true'
taxon_file_final = taxon_file_final[taxon_file_final['taibif_accepted_namecode']!='']

for i in taxon_file_final.index:
    if float(taxon_file_final.loc[i,'taibif_accepted_namecode']) != float(taxon_file_final.loc[i,'taibif_namecode']):
        taxon_file_final.loc[i,'is_accepted_name'] = 'false'



# 匯入語法
taxon_file_final = taxon_file_final.rename(columns = {'taibif_accepted_namecode':'source_id','taibif_namecode':'accepted_name_id'})

b = taxon_file_final[taxon_file_final['source_id']!='']
for i in b.index:
    b.loc[i,'source_id'] = str(b.loc[i,'source_id']).replace('.0','')

b.to_csv(f'./gbif_highertaxon.csv')

a = taxon_file_final[taxon_file_final['source_id']=='']
a.to_csv(f'./error_taxon.csv')