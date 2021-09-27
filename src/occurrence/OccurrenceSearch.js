import React from 'react';

export default function OccurrenceSearch(props) {
  //console.log(props);
  const rows = props.data.results.map((row, index) => {
    const sn = props.data.offset + index + 1;
    const countryOrLocality = [row.country, row.locality].join('/');
    return (
        <tr key={index}>
        <td><a href={"/occurrence/"+row.taibif_occ_id}>{ sn }</a></td>
        <td>{/*http://taibif.tw/zh/namecode/{{ i.name_code */}{ row.scientific_name }</td>
        <td>{ row.vernacularName }</td>
        <td>{ row.eventDate }</td>
        <td>{ countryOrLocality }</td>
        <td><a href={"/dataset/"+row.taibif_dataset_name+"/"}>{ row.taibif_dataset_name_zh }</a></td>
        <td>{ row.kingdom }</td>
        <td>{ row.phylum }</td>
        <td>{ row.class }</td>
        <td>{ row.order }</td>
        <td>{ row.family }</td>
        <td>{ row.genus }</td>
        <td>{ row.species }</td>
        </tr>
    )
  });
  //  download link
  /*const downloadLink = (props.downloadUrl !== '') ?
        <a href={props.downloadUrl} className="btn btn-primary" target="_blank">下載篩選結果 (CSV)</a> :
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>; */
  return (
      <div className="table-responsive">
        <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>學名</th>
            <th>俗名</th>
            <th>時間</th>
            <th>國家/地區</th>
            <th>資料集</th>
            <th>界</th>
            <th>門</th>
            <th>綱</th>
            <th>目</th>
            <th>科</th>
            <th>屬</th>
            <th>種</th>
          </tr>
        </thead>
        <tbody>
        {rows}
        </tbody>
        </table>
      </div>
  );
}
