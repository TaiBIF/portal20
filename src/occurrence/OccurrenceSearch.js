import React from 'react';

export default function OccurrenceSearch(props) {
  const rows = props.data.results.map((row, index) => {
    const sn = props.data.offset + index + 1;
    return (
        <tr key={index}>
        <td><a href={"/occurrence/"+row.taibif_id}>{ sn }</a></td>
        <td>{/*http://taibif.tw/zh/namecode/{{ i.name_code */}{ row.scientific_name }</td>
        <td>{ row.vernacular_name }</td>
        <td>{ row.date }</td>
        <td>{ row.country }{/*/ i.locality */}</td>
        <td><a href={"/dataset/"+row.dataset+"/"}>{ row.dataset }</a></td>
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
          </tr>
        </thead>
        <tbody>
        {rows}
        </tbody>
        </table>
      </div>
  );
}
