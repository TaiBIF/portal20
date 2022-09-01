import React from 'react';
import { makeStyles } from '@material-ui/core/styles';

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
                      "MaterialCitation"]
  const rows = props.data.results.map((row, index) => {
    const sn = props.data.offset + index + 1;
    const countryOrLocality = [row.taibif_country, row.locality].join('/');
    

    const bor = bor_allow.includes(row.basisOfRecord) ? row.basisOfRecord : "";
    return (
        <tr key={index} onClick={(e)=>{window.location.href=`/occurrence/${row.taibif_occ_id}`}} className={classes.occurrenceRow}>
        <td>{ sn }</td>
        <td>{ row.vernacularName }</td>
        <td >{/*http://taibif.tw/zh/namecode/{{ i.name_code */}{ row.scientificName }</td>
        <td>{ row.eventDate }</td>
        <td>{ countryOrLocality }</td>
        <td><a href={"/dataset/"+row.taibif_dataset_name+"/"}>{ row.taibif_dataset_name_zh }</a></td>
        <td>{ bor }</td>
        <td>{ row.kingdom }</td>
        <td>{ row.phylum }</td>
        <td>{ row.class }</td>
        <td>{ row.order }</td>
        <td>{ row.family }</td>
        <td style={{fontStyle: "italic"}}> { row.genus }</td>
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
