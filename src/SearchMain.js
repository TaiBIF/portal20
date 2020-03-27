import React from 'react';

function SearchMainOccurrence(props) {
  //console.log(props);
  const rows = props.data.results.map((row, index) => {
    return (
        <tr key={row.taibif_id}>
        <td><a href={"/occurrence/"+row.taibif_id}>{ index+1 }</a></td>
        <td>{/*http://taibif.tw/zh/namecode/{{ i.name_code */}{ row.scientific_name }</td>
        <td>{ row.vernacular_name }</td>
        <td>{ row.basis_of_record }</td>
        <td>{ row.country }{/*/ i.locality */}</td>
        <td><a href={"/dataset/"+row.dataset.name+"/"}>{ row.dataset.title }</a></td>
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

  return (
      <div className="col-xs-12 col-md-9">
      <div className="container">
        <h2>出現紀錄<small>{/* / 共 occurrence_list.paginator.count  筆資料 */} 搜尋時間: { props.data.elapsed }秒</small></h2>
        <div className="loading-overlay"></div>
        <div className="search-main-tag-wrapper">篩選條件: <div className="search-main-tag-item">{ filterTags }</div></div>
      <table className="table table-hover">
        <thead>
          <tr>
            <th>#</th>
            <th>學名</th>
            <th>俗名</th>
            <th>紀錄依據</th>
            <th>國家/地區</th>
            <th>資料集</th>
          </tr>
        </thead>
        <tbody>
      {rows}
        </tbody>
      </table>
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
        <h3 className="listbox-inner-title"><a href={"/species/"+row.id} className="">{row.name_zh} { row.name }</a></h3>
        <p className="listbox-inner-summary hidden-xs">
        {row.description}
        </p>
        <span className="badge"> {row.rank} </span>
        {(row.is_accepted_name) ? <span className="badge">有效的</span> : ''}
        <span className="badge">物種數: {row.count} </span>
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
export {SearchMainDataset, SearchMainOccurrence, SearchMainPublisher, SearchMainSpecies};
