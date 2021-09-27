import React from 'react';

import OccurrenceRouter from './occurrence/OccurrenceRouter';
import {
  filtersToSearch,
  Pagination,
} from './Utils'

function SpeciesOther(props) {
  const {q} = props;
  return (
      <React.Fragment>
      <h3>相關資料庫列表</h3>
      <ul>
      <li><a href={"https://www.tbn.org.tw/taxa?name="+q} target="_blank">TBN 台灣生物多樣性網絡</a></li>
      <li><a href={"https://taieol.tw/search_list/name/"+q} target="_blank">TaiEOL 臺灣生命大百科</a></li>
      <li><a href={"https://www.inaturalist.org/search?q="+q} target="_blank">iNaturalist</a></li>
      <li><a href={"https://www.gbif.org/species/search?q="+q} target="_blank">GBIF</a></li>
      <li><a href={"https://www.ipni.org/?q="+q} target="_blank">IPNI</a></li>
      </ul>
      </React.Fragment>
  )
}

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
              )}
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


function PublisherResult(props) {
  const rows = props.data.results.map((row, index) => {
    const link = `/publisher/${row.id}/`;
    const publisherImage = null;
    // TODO
    //<a href={link}><img src="images/logo-sinica.jpg" class="img-responsive"></a>
    return (
        <div className="row listbox-img-right-wrapper" key={index}>
          <div className="col-lg-10 col-md-9 col-xs-8">
            <h3 className="listbox-inner-title"><a href={link}>{row.name}</a></h3>
            <div className="listbox-inner-summary">
            <a href={link}>{row.description}</a>
            </div>
          </div>
          <div className="col-lg-2 col-md-3 col-xs-4">
         {publisherImage}
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

const SEARCH_TYPE_LABEL_MAP = {
  'occurrence': '出現紀錄',
  'dataset': '資料集',
  'publisher': '發布者',
  'species': '物種',
}

function SearchMain(props) {
  //console.log(props, 'main');
  let initActiveTab = 'menu1';
  if (window.location.pathname === '/occurrence/taxonomy/') {
    initActiveTab = 'menu5';
  }
  const [tabActive, setTabActive] = React.useState(initActiveTab);
  const countString = (props.data && props.data.count ) ? props.data.count.toLocaleString('en') : 0;
  const elapsed = (props.data && props.data.elapsed ) ? props.data.elapsed.toFixed(2) : '';

  const typeLabel
        = SEARCH_TYPE_LABEL_MAP[props.searchType];

  let q = null;
  const filterTags = [];
  for (let f of props.filters) {
    const menuKey = f.split('=');
    const found = props.menus.find((x) => x['key'] === menuKey[0]);
    if (found) {
      const tagLabel = `${found['label']}: ${decodeURIComponent(menuKey[1])}`;
      filterTags.push((<span key={tagLabel} className="search-content-sort-tag">{ tagLabel }</span>));
    }
    else if (menuKey[0] === 'q') {
      q = decodeURIComponent(menuKey[1]);
      filterTags.push((<span key="q" className="search-content-sort-tag">關鍵字:{ q }</span>));
    }
  }

  function toggleTab(e, menu) {
    e.preventDefault()
    setTabActive(menu);
  }

  let tabNavs = null;
  if (props.searchType === 'occurrence') {
    tabNavs = null;
  } else if (props.searchType === 'dataset') {
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
  } else if (props.searchType == 'species') {
    tabNavs = (
        <div className="table-responsive">
          <ul className="nav nav-tabs search-content-tab">
            <li className={tabActive == "menu1" ? "active": null}><a data-toggle="tab" onClick={(e)=>toggleTab(e, 'menu1')}>資料列表</a></li>
            {q
             ? <li className={tabActive == "menu2" ? "active" : null}><a data-toggle="tab" onClick={(e)=>toggleTab(e, 'menu2')}>瀏覽其他資料庫</a></li>
             : null
            }
          </ul>
        </div>)
  } else if (props.searchType === 'publisher') {
    tabNavs = (
        <div className="table-responsive">
          <ul className="nav nav-tabs search-content-tab">
            <li className="active"><a data-toggle="tab">全部</a></li>
          </ul>
        </div>);
  }

  let pageUrlPrefix = `/${props.searchType}/search/`;
  const qs = filtersToSearch(props.filters, true);
  if (qs.length > 0) {
    pageUrlPrefix = `${pageUrlPrefix}?${qs}`;
  }
  console.log(pageUrlPrefix);

  return (
      <div className="search-content">
        <ol className="breadcrumb">
          <li><a href="/">首頁</a></li>
          <li className="active">搜尋{typeLabel}</li>
        </ol>
        <div className="search-content-heading-wrapper">
      <h1 className="heading-lg">{typeLabel} <span className="heading-footnote">共 {countString} 筆資料 ({elapsed} 秒)</span></h1>
          <span>篩選條件：</span>
          {filterTags}
        </div>
      {(props.searchType !== 'occurrence') ?
        <React.Fragment>
        {tabNavs}
        <div className="tab-content">
          <div id="menu1" className="tab-pane fade in active">
          {props.searchType === 'dataset'
           ? <DatasetResult data={props.data} /> : null}
          {(props.searchType === 'species' && tabActive === 'menu1')
           ? <SpeciesResult data={props.data} /> : null}
          {(props.searchType === 'species' && tabActive === 'menu2' && q)
           ? <SpeciesOther q={q}/> : null}
          {props.searchType === 'publisher'
           ? <PublisherResult data={props.data} /> : null}
          {props.data.count > 0 ? props.pagination: null}
           </div>
         </div>
         </React.Fragment>
       : <OccurrenceRouter data={props.data} filters={props.filters}/>
      }
      <Pagination offset={props.data.offset} total={props.data.count} urlPrefix={pageUrlPrefix} />
      {/*<Pagination offset={100} total={121} urlPrefix={pageUrlPrefix} />*/}
      </div>
  );
}

export default SearchMain;
