import React from 'react';

function StyledScientificName(props) {
  const {data} = props;
  let name = data.name;
  if (data.rank === 'species') {
    const match3 = data.name_full.match('(^[A-Z]{1}[a-z]+) ([a-z]+) ([a-z]+\.) ([a-z]+)(.*)');
    if (match3) {
      name = <React.Fragment><i>{match3[1]} {match3[2]} </i> {match3[3]} <i>{match3[4]}</i> {match3[5]}</React.Fragment>;
    } else {
      const match2 = data.name_full.match('(^[A-Z]{1}[a-z]+) ([a-z]+)(.*)');
      if (match2) {
        name = <React.Fragment><i>{match2[1]} {match2[2]} </i> {match2[3]}</React.Fragment>
      }
    }
  }
  return (<React.Fragment>{name} {data.name_zh}</React.Fragment>)
}

function SpeciesResult(props) {
  const rows = props.data.results.map((row, index) => {
    const link = `/species/${row.id}/`;
    // TODO species image
      // <a href="05-searchPublisher.html"><img src="images/logo-sinica.jpg" class="img-responsive"></a>
    const imgLink = null;
    return (
        <div className="row listbox-img-right-wrapper" key={index}>
          <div className="col-xs-8">
        <h3 className="listbox-inner-title"><a href={link}><StyledScientificName data={row} /></a></h3>
                  <div className="listbox-inner-summary hidden-xs">
                  <ul className="scientific-name-wrapper">
        { row.rank_list.map((t)=> 
                            <li key={t.id}><a href={"/species/"+t.id}>{t.name} {t.name_zh}</a></li>
        )
        }
        <li><a href={link}><StyledScientificName data={row} /></a></li>
                    </ul>
        </div>
        {row.is_accepted_name
         ? <span className="listbox-inner-tag"><a href="">有效的</a></span>
         : null}
                </div>
          <div className="col-xs-4">
            {imgLink}
          </div>
        </div>)
  });
  return (
    <div className="container-fluid search-content-grid-wrapper">
      {rows}
    </div>
  );
}

function DatasetResult(props) {
  const rows = props.data.results.map((row, index) => {
    const num_record = row.num_record.toLocaleString('en');
    const link = `/dataset/${row.name}/`;
    // TODO
    // before <span> 紀錄數量
    //  <span className="listbox-inner-tag"><a href="#">引用次數：48</a></span>
    return (
        <div className="row listbox-img-right-wrapper" key={index}>
          <div className="col-xs-12">
            <span className="search-content-list-tag">{row.dwc_type}</span>
            <h3 className="listbox-inner-title"><a href={link}>{row.title}</a></h3>
            <span className="listbox-inner-date">{row.publisher}</span>
            <div className="listbox-inner-summary hidden-xs">
            <a href={link}>{row.description}</a>
            </div>
            <span className="listbox-inner-tag"><a href="#">記錄數量：{num_record} </a></span>
          </div>
        </div>
    )
  });
  return (
      <div className="container-fluid search-content-grid-wrapper">
      {rows}
      </div>
  );
}

function OccurrenceResult(props) {
  //console.log(props);
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
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>;
  */
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
const SEARCH_TYPE_LABEL_MAP = {
  'occurrence': '出現紀錄',
  'dataset': '資料集',
  'publisher': '發布者',
  'species': '物種',
}

function SearchMain(props) {
  //console.log(props, 'main');
  const count = props.data.count.toLocaleString('en');
  const typeLabel = SEARCH_TYPE_LABEL_MAP[props.searchType];

  const filterTags = [];
  for (let f of props.filters) {
    const menuKey = f.split('=');
    const found = props.menus.find((x) => x['key'] === menuKey[0]);
    if (found) {
      const tagLabel = `${found['label']}: ${menuKey[1]}`;
      filterTags.push((<span key={tagLabel} className="search-content-sort-tag">{ tagLabel }</span>));
    }
    else if (menuKey[0] === 'q') {
      const q = decodeURIComponent(menuKey[1]);
      filterTags.push((<span key="q" className="search-content-sort-tag">關鍵字:{ q }</span>));
    }
  }


  let tabNavs = null;
  if (props.searchType === 'dataset') {
    let act = 'all';
    for (let f of props.filters) {
      if (f.indexOf('core=') >= 0) {
        act = f.split('=')[1];
      }
    }
    tabNavs = (
        <div className="table-responsive">
          <ul className="nav nav-tabs nav-justified search-content-tab">
            <li className={act=="all" ? "active": null}><a data-toggle="tab" onClick={(e)=>props.onClickTab(e, 'all')}>全部</a></li>
            <li className={act=="occurrence" ? "active" : null}><a data-toggle="tab" onClick={(e)=>props.onClickTab(e, 'occurrence')}>出現紀錄</a></li>
            <li className={act=="taxon" ? "active" : null}><a data-toggle="tab" onClick={(e)=>props.onClickTab(e, 'taxon')}>物種名錄</a></li>
            <li className={act=="event" ? "active" : null}><a data-toggle="tab" onClick={(e)=>props.onClickTab(e, 'event')}>調查活動</a></li>
            <li className={act=="meta" ? "active": null}><a data-toggle="tab" onClick={(e)=>props.onClickTab(e, 'meta')}>詮釋資料</a></li>
          </ul>
        </div>)
  }
  return (
      <div className="search-content">
        <ol className="breadcrumb">
          <li><a href="/">首頁</a></li>
          <li className="active">搜尋{typeLabel}</li>
        </ol>
        <div className="search-content-heading-wrapper">
          <h1 className="heading-lg">{typeLabel} <span className="heading-footnote">共 {count} 筆資料</span></h1>
          <span>篩選條件：</span>
          {filterTags}
        </div>
        {tabNavs}
        <div className="tab-content">
          <div id="menu1" className="tab-pane fade in active">
          {props.searchType === 'occurrence'
           ? <OccurrenceResult data={props.data} /> : null}
          {props.searchType === 'dataset'
           ? <DatasetResult data={props.data} /> : null}
          {props.searchType === 'species'
           ? <SpeciesResult data={props.data} /> : null}
          {props.searchType === 'publisher'
           ? <PublisherResult data={props.data} /> : null}
          {props.data.count > 0 ? props.pagination: null}
          </div>
        </div>
      </div>
  );
}

export default SearchMain;
