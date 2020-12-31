import React from 'react';
import { CSVLink, CSVDownload } from "react-csv";




function OccurrenceDownload(props) {
  const Occur = props.data.results;
  const length = Occur.length;
  let downloadLink;
  if (length < 50) {
      downloadLink =  <div className="btn btn-primary disabled">已下載篩選結果 (CSV)</div>
  } else {
      downloadLink = <div className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</div>
  }
  //  download link
  /*const downloadLink = (props.downloadUrl !== '') ?
        <a href={props.downloadUrl} className="btn btn-primary" target="_blank">下載篩選結果 (CSV)</a> :
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>; */

  return (
      <div className="table-responsive">
        <CSVDownload
            data={Occur}
            target="_blank"/>

        {downloadLink}
      </div>
  );
}
export {OccurrenceDownload, }
