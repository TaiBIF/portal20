import React from 'react';
import Accordion from "./components/Accordion";

function SearchSidebar(props) {
  //console.log(props);
  const menuList = props.menus.map(function(m) {
    const menu_items = m.rows.map(function(x) {
      const itemChecked = props.filters.has(`${m.key}.${x.key}`);
      return (<div key={x.key} className="menu-item">
              <div className="menu-item__title">
              <input type="checkbox" onChange={(e)=> {e.persist(); props.onClick(e, m.key, x.key)}} checked={itemChecked} /> {x.label}
              </div>
              <div className="menu-item__count">
              {x.count}
              </div>
              </div>);
    });
    return (
        <Accordion key={m.key} title={m.label} content={menu_items} />
    )
  });
  const numFilters = props.filters.size === 0 ? '' : <span className="num-filters badge">{props.filters.size}</span>;
  let searchTypeLabel = '';
  if (props.searchType === 'dataset') {
    searchTypeLabel = '資料集';
  }
  if (props.searchType === 'occurrence') {
    searchTypeLabel = '出現紀錄';
  }
  return (
      <div className="col-xs-6 col-md-3 search-sidebar">
      <div className="search-sidebar__title search-sidebar__title--head">
      <span>{searchTypeLabel}</span>
      <div className="clear-filters" data-toggle="tooltip" data-placement="left" title="清除" onClick={props.onClickClear}>
      {numFilters}
      <span className="glyphicon glyphicon-trash"></span>
      </div>
      </div>
      <div className="input-group">
      <input className="form-control search-keyword" placeholder="搜尋關鍵字" name="srch-term" id="srch-term" type="text" value={props.queryKeyword} onChange={props.onChangeKeyword}/>
      <div className="input-group-btn">
      <button className="btn btn-default search-keyword-sign" type="submit" onClick={props.onClickSubmitKeyword}><i className="glyphicon glyphicon-search"></i></button>
      </div>
      </div>
      {menuList}
      </div>)
}

export default SearchSidebar;
