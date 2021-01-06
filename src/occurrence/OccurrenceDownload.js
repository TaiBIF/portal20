import React from 'react';
import { CSVLink, CSVDownload } from "react-csv";


function OccurrenceDownload(props) {
  const Occur = props.data.results;
  const length = Occur.length;
  let downloadLink;
  if (length < 5000) {
      downloadLink =  <div className="btn btn-primary">下載篩選結果 (CSV)</div>
  } else {
      downloadLink = <div className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</div>
  }
  //  download link
  /*const downloadLink = (props.downloadUrl !== '') ?
        <a href={props.downloadUrl} className="btn btn-primary" target="_blank">下載篩選結果 (CSV)</a> :
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>; */
  const now = new Date();
  const TzOffsetSecond = -now.getTimezoneOffset() * 60;
  const deltaNow = new Date(now.getTime() + TzOffsetSecond);
  const d = deltaNow.toISOString().split('.')[0].split('T');
  const dateStr = [
    d[0].split('-').join(''),
    d[1].replace(/:/gi, '')
  ].join('_');
  //console.log(dateStr);
  return (
      <div className="table-responsive">
        <CSVLink
            data={Occur}
            target="_blank"
            filename={"taibif-data" + dateStr + ".csv"}
         >
            {downloadLink}
        </CSVLink>
      </div>
  );
}
export {OccurrenceDownload, }
