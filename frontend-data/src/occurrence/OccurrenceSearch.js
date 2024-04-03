import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Parser from 'html-react-parser';

const useStyles = makeStyles({
  occurrenceRow: {
    '&:hover': {
      backgroundColor: '#eeeeee',
      cursor: 'pointer',
    }
  },
});

export default function OccurrenceSearch(props) {
  // console.log(props);
  const classes = useStyles();
  const bor_allow = ["PreservedSpecimen", 
                      "FossilSpecimen",
                      "LivingSpecimen",
                      "MaterialSample",
                      "Event",
                      "HumanObservation",
                      "MachineObservation",
                      "Taxon",
                      "Occurrence",
                      "MaterialCitation",
                      '材料實體',
                      '保存標本',
                      '化石標本',
                      '活體標本',
                      '人為觀測',
                      '材料樣本',
                      '機器觀測',
                      '調查活動',
                      '名錄/分類群',
                      '出現紀錄',
                      '文獻紀錄'
                    ]
  
  
  const test_row = {
      "Taiwan":"台灣",
      "China":"中國",
      "Japan":"日本",
      "Nepal":"尼泊爾",
      "Burundi":"蒲隆地",
      "Republic of India":"印度",
      "Vietnam":"越南",
      "Philippines":"菲律賓",
      "Thailand":"泰國",
      "United States":"美國",
      "Tanzania":"坦尚尼亞",
      "Australia":"澳洲",
      "United Kingdom":"英國",
      "Indonesia":"印尼",
      "Bolivia":"玻利維亞",
      "Myanmar":"緬甸",
      "Malaysia":"馬來西亞",
      "India":"印度",
      "New Zealand":"紐西蘭",
      "Falkland Islands":"福克蘭群島",
      "Ecuador":"厄瓜多",
      "Uganda":"烏干達",
      "Russia":"俄羅斯",
      "Canada":"加拿大",
      "Papua New Guinea":"巴布亞紐幾內亞 ",
      "Colombia":"哥倫比亞",
      "Sudan":"蘇丹",
      "Mexico":"墨西哥",
      "Argentina":"阿根廷",
      "Democratic Socialist Republic of Sri Lanka":"斯里蘭卡",
      "Kenya":"肯亞",
      "South Korea":"南韓",
      "North Korea":"北韓",
      "Costa Rica":"哥斯大黎加",
      "Kyrgyzstan":"吉爾吉斯",
      "Georgia":"喬治亞",
      "Libya":"利比亞",
      "Panama":"巴拿馬",
      "Republic of Indonesia":"印尼",
      "Cambodia":"柬埔寨",
      "Chile":"智利",
      "Ethiopia":"衣索比亞",
      "Islamic Republic of Pakistan":"巴基斯坦",
      "Italy":"義大利",
      "Mauritius":"模里西斯",
      "Northern Mariana Islands":"北馬利安納群島",
      "Peru":"秘魯",
      "United States of America":"美國",
      "Chad":"查德",
      "Dominica":"多米尼克",
      "French Polynesia":"法屬玻里尼西亞",
      "Ghana":"迦納",
      "Guatemala":"瓜地馬拉",
      "Kazakhstan":"哈薩克",
      "Laos":"寮國",
      "Madagascar":"馬達加斯加",
      "Nigeria":"奈及利亞",
      "Paraguay":"巴拉圭",
      "Shaksgam Valley":"克里青河谷",
      "Spratly Islands":"南沙群島",
      "Sri Lanka":"斯里蘭卡",
      "Tajikistan":"塔吉克",
      "Uzbekistan":"烏茲別克",
  };
  const map2 = new Map(Object.entries(test_row));
 
  const rows = props.data.results.map((row, index) => {
    const sn = props.data.offset + index + 1;
    const vernacular_name = row.taibif_vernacularName ? row.taibif_vernacularName : '';
    const eventDate = row.taibif_eventDate ? row.taibif_eventDate : '';
    const country_ch = map2.get(row.taibif_country);
    const countryOrLocality = (props.language === 'zh-hant') ? [country_ch, row.locality].join('/') : [row.taibif_country, row.locality].join('/');
    const bor = bor_allow.includes(row.taibif_basisOfRecord) ? row.taibif_basisOfRecord : row.basisOfRecord;
    const datasetKey = row.taibif_datasetKey ? row.taibif_datasetKey : ''

    return (
        <tr key={index} onClick={(e)=>{window.location.href=`/occurrence/${row.taibif_occ_id}`}} className={classes.occurrenceRow}>
        <td>{ sn }</td>
        <td>{ vernacular_name }</td>
        <td>{(row.taibif_formattedName ? Parser(row.taibif_formattedName):'')}</td>
        <td>{ eventDate }</td>
        <td>{ countryOrLocality }</td>
        <td><a href={"/dataset/"+datasetKey+"/"}>{ row.taibif_dataset_name_zh }</a></td>
        <td>{ bor }</td>
        <td>{ row.taibif_kingdom }</td>
        <td>{ row.taibif_phylum }</td>
        <td>{ row.taibif_class }</td>
        <td>{ row.taibif_order }</td>
        <td>{ row.taibif_family }</td>
        <td style={{fontStyle: "italic"}}> { row.taibif_genus }</td>
        </tr>
    )
  });
  
  
  let columnName = null;
  if (props.language === 'zh-hant'){
    columnName = 
  (<thead>
          <tr>
            <th>#</th>
            <th style={{'width': '100px'}}>俗名</th>
            <th>對應有效學名</th>
            <th>日期</th>
            <th>國家/地區</th>
            <th>資料集</th>
            <th>紀錄類型</th>
            <th>界</th>
            <th>門</th>
            <th>綱</th>
            <th>目</th>
            <th>科</th>
            <th>屬</th>
          </tr>
    </thead>)}
    else if (props.language === 'en'){
      columnName = (
      <thead>
          <tr>
            <th>#</th>
            <th>Common Name</th>
            <th>Scientfic Name</th>
            <th>Date</th>
            <th>Country or Area</th>
            <th>Dataset</th>
            <th>Basic of Record</th>
            <th>Kingdom</th>
            <th>Pyhlum</th>
            <th>Class</th>
            <th>Family</th>
            <th>Order</th>
            <th>Genus</th>
          </tr>
    </thead>)
    }
  //  download link
  /*const downloadLink = (props.downloadUrl !== '') ?
        <a href={props.downloadUrl} className="btn btn-primary" target="_blank">下載篩選結果 (CSV)</a> :
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>; */
  return (
      <div className="table-responsive">
        <table className="table">
        
            {columnName}
          
        <tbody>
        {rows}
        </tbody>
        </table>
      </div>
  );
}
