import React from 'react';
//import { CSVLink, CSVDownload } from "react-csv";
import {filtersToSearch} from '../Utils';

function OccurrenceDownload(props) {
  const queryString = filtersToSearch(props.filters);

  // 用 Django 的 view 回傳, 而不是 react 得到的分頁資料
  
  //const Occur = props.data.results;
  //const length = Occur.length;
  //console.log(queryString);
  //if (length < 5000) {
  //} else {
  //    downloadLink = <div className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</div>
  //}
  //  download link
  /*const downloadLink = (props.downloadUrl !== '') ?
        <a href={props.downloadUrl} className="btn btn-primary" target="_blank">下載篩選結果 (CSV)</a> :
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>; */
  /*
  const now = new Date();
  const TzOffsetSecond = -now.getTimezoneOffset() * 60;
  const deltaNow = new Date(now.getTime() + TzOffsetSecond);
  const d = deltaNow.toISOString().split('.')[0].split('T');
  const dateStr = [
    d[0].split('-').join(''),
    d[1].replace(/:/gi, '')
  ].join('_');
  //console.log(dateStr);
  */
  /*
          <CSVLink
            data={Occur}
            target="_blank"
            filename={"taibif-data" + dateStr + ".csv"}
    >
            </CSVLink>
  */
  return (
      <div className="table-responsive">
      <a className="btn btn-primary" target="_blank" href={"/search/occurrence/download/?"+queryString}>下載篩選結果 (CSV)</a>
      </div>
  );
}
export {OccurrenceDownload, }
