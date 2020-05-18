import React from 'react';

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
    let act = '';
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
          {props.data.count > 0 ? props.pagination: null}
          </div>
        </div>
      </div>
  );
}
function SearchMainOccurrence(props) {
  //console.log(props);
  const rows = props.data.results.map((row, index) => {
    const sn = props.data.offset + index + 1;
    return (
        <tr key={row.taibif_id}>
        <td><a href={"/occurrence/"+row.taibif_id}>{ sn }</a></td>
        <td>{/*http://taibif.tw/zh/namecode/{{ i.name_code */}{ row.scientific_name }</td>
        <td>{ row.vernacular_name }</td>
        <td>{ row.date }</td>
        <td>{ row.country }{/*/ i.locality */}</td>
        <td><a href={"/dataset/"+row.dataset+"/"}>{ row.dataset }</a></td>
        </tr>
    )
  });

  const filterTags = [];
  for (let f of props.filters) {
    const menuKey = f.split('.');
    const found = props.menus.find((x) => x['key'] === menuKey[0]);
    if (found) {
      const tagLabel = `${found['label']}: ${menuKey[1]}`;
      filterTags.push((<span key={tagLabel} className="badge search-tag">{ tagLabel }</span>));
    }
    else if (menuKey[0] === 'q') {
      const q = decodeURIComponent(menuKey[1]);
      filterTags.push((<span key="q" className="badge search-tag">關鍵字:{ q }</span>));
    }
  }

  const elapsed = props.data.elapsed.toFixed(2);

  const downloadLink = (props.downloadUrl !== '') ?
        <a href={props.downloadUrl} className="btn btn-primary" target="_blank">下載篩選結果 (CSV)</a> :
        <button className="btn btn-primary disabled">資料量太大，無法下載，請縮小搜尋範圍</button>;
  return (
      <div className="col-xs-12 col-md-9">
      <div className="container">
      <h2>出現紀錄<small> {props.data.count}  筆資料 / 搜尋時間: { elapsed } 秒</small></h2>
      <div className="search-main-tag-wrapper">篩選條件: <div className="search-main-tag-item">{ filterTags }</div></div>

      <table className="table table-hover">
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
      {downloadLink}
      </div>
      </div>
  )
}

function SearchMainDataset(props) {
  //console.log(props);
  const rows = props.data.results.map((row) => {
    return (
        <div className="row listbox-img-right-wrapper" key={row.id}>
        <div className="col-xs-8">
        <span className="label label-warning">{row.dwc_core_type}</span>
        <h3 className="listbox-inner-title">{ row.title }</h3>
        <p className="listbox-inner-summary hidden-xs">
        {row.description}
        </p>
        <span className="badge">紀錄數量: {row.num_record} </span>
        <div><a href={"/dataset/"+row.name} className="">觀看資料集</a></div>
        </div>
        </div>
    )
  });

  let activeTabList = ['active', '', '', '', ''];
  //console.log(props.filters);
  const filterTags = [];
  for (let f of props.filters) {
    if (f.indexOf('core.') >= 0) {
      activeTabList[0] = '';
      activeTabList[1] = (f === 'core.occurrence') ? 'active' : '';
      activeTabList[2] = (f === 'core.taxon') ? 'active' : '';
      activeTabList[3] = (f === 'core.event') ? 'active' : '';
      activeTabList[4] = (f === 'core.meta') ? 'active' : '';
    }
    else {
      const menuKey = f.split('.');
      const found = props.menus.find((x) => x['key'] === menuKey[0]);
      if (found) {
        const tagLabel = `${found['label']}: ${menuKey[1]}`;
        filterTags.push((<span key={tagLabel} className="badge search-tag">{ tagLabel }</span>));
      }
      else if (menuKey[0] === 'q') {
        const q = decodeURIComponent(menuKey[1]);
        filterTags.push((<span key="q" className="badge search-tag">關鍵字: {q}</span>));
      }
    }
  }
  return (
      <div className="col-xs-12 col-md-9">
      <div className="container">
      <h2 className="heading-lg-ul">資料集
      <span className="heading-footnote"> 共 {props.data.count} 筆資料</span>
      </h2>
      <div className="search-main-tag-wrapper">篩選條件: <div className="search-main-tag-item">{ filterTags }</div></div>
      <ul className="nav nav-tabs search-menu-tabs">
      <li className={activeTabList[0]}><a href="#" onClick={(e)=>props.onClickTab(e, 'all')}>全部</a></li>
      <li className={activeTabList[1]}><a href="#" onClick={(e)=>props.onClickTab(e, 'occurrence')}>出現紀錄</a></li>
      <li className={activeTabList[2]}><a href="#" onClick={(e)=>props.onClickTab(e, 'taxon')}>物種名錄</a></li>
      <li className={activeTabList[3]}><a href="#" onClick={(e)=>props.onClickTab(e, 'event')}>調查活動</a></li>
      <li className={activeTabList[4]}><a href="#" onClick={(e)=>props.onClickTab(e, 'meta')}>詮釋資料</a></li>
      </ul>
      {rows}
      </div>
      </div>
  )
}

function SearchMainPublisher(props) {
  //console.log(props);
  const rows = props.data.results.map((row) => {
    return (
        <div className="row listbox-img-right-wrapper" key={row.id}>
        <div className="col-xs-8">
        <h3 className="listbox-inner-title">{ row.name }</h3>
        <p className="listbox-inner-summary hidden-xs">
        {row.description}
        </p>
        <span className="badge">資料集數量: {row.num_dataset} </span>
        <div><a href={"/publisher/"+row.id} className="">發布者</a></div>
        </div>
        </div>
    )
  });

  const filterTags = [];
  for (let f of props.filters) {
    const menuKey = f.split('.');
    if (menuKey[0] === 'q') {
      const q = decodeURIComponent(menuKey[1]);
      filterTags.push((<span key="q" className="badge search-tag">關鍵字: {q}</span>));
    }
  }
  return (
      <div className="col-xs-12 col-md-9">
      <div className="container">
      <h2 className="heading-lg-ul">發布者
      <span className="heading-footnote"> 共 {props.data.count} 筆資料</span>
      </h2>
      <div className="search-main-tag-wrapper">篩選條件: <div className="search-main-tag-item">{ filterTags }</div></div>
      {rows}
      </div>
      </div>
  )
}

function SearchMainSpecies(props) {
  //console.log(props);
  const rows = props.data.results.map((row) => {
    return (
        <div className="row listbox-img-right-wrapper" key={row.id}>
        <div className="col-xs-8">
        <h3 className="listbox-inner-title"><a href={"/species/"+row.id} className="">{row.name_zh} { row.name_full }</a></h3>
        <p className="listbox-inner-summary hidden-xs">
        {row.description}
        </p>
        <span className="label label-primary" style={{'margin': '0 2px'}}> {row.rank} </span>
        {(row.is_accepted_name) ? <span className="label label-success" style={{'margin': '0 2px'}}>有效的</span> : ''}
        <span className="label label-default" style={{'margin': '0 2px'}}>物種數: {row.count} </span>
        </div>
        </div>
    )
  });

  const filterTags = [];
  for (let f of props.filters) {
    const menuKey = f.split('.');
    if (menuKey[0] === 'q') {
      const q = decodeURIComponent(menuKey[1]);
      filterTags.push((<span key="q" className="badge search-tag">關鍵字: {q}</span>));
    }
  }
  return (
      <div className="col-xs-12 col-md-9">
      <div className="container">
      <h2 className="heading-lg-ul">物種
      <span className="heading-footnote"> 共 {props.data.count} 筆資料</span>
      </h2>
      <div className="search-main-tag-wrapper">篩選條件: <div className="search-main-tag-item">{ filterTags }</div></div>
      {rows}
      </div>
      </div>
  )
}
export {SearchMainDataset, SearchMainOccurrence, SearchMainPublisher, SearchMainSpecies, SearchMain, OccurrenceResult};
