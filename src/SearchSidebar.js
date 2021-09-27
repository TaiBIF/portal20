import React, {useState, useRef} from 'react';
//import Accordion from "./components/Accordion";
//import Tree from "./components/Tree";
import SearchTaxon from './SearchSidebarTaxon';
import Slider from '@material-ui/core/Slider';

function Accordion(props) {
  const [isOpen, setOpenState] = useState(false);
  const [yearRange, setYearRange] = useState([1900, 2021]); /* TODO */
  const sliderMarks = [];
  for (let i=1900; i<2022; i++) {
    sliderMarks.push({value: i, label: i});
  }


  const {content, onClick, filters} = props;

  const appendClass = (props.appendClass) ? ` ${props.appendClass}` : '';
  function toggleAccordion(e) {
    e.preventDefault()
    setOpenState(isOpen === false ? true : false);
  }

  const handleSliderCommitted = (event) => {
    //console.log(yearRange);
    onClick(event, content.key, yearRange.join(','))
  };

  const menuItems = content.rows.map((x) => {
    if(content.key ===  'year'){
        const [yearValue, setYearValue] = useState([x.year_start, x.year_end]);
        const handleChange = (event, newValue) => {
          setYearValue(newValue);
          onClick(event, content.key, newValue);
        };
        // console.log(content.key, handleChange)
        return (
          <div className="year_test" key={x.key}>
            <Slider
              value={yearRange}
              onChange={(e, newRange) => setYearRange(newRange)}
              onChangeCommitted={handleSliderCommitted}
              max={2021}
              min={1900}
              valueLabelDisplay="auto"
              aria-labelledby="range-slider"
            />
          </div>
        );
    }else{
      const count = (x.count) ? x.count.toLocaleString() : null;
      const itemChecked = filters.has(`${content.key}=${x.key}`);
      return (
          <div className="search-sidebar-checkbox-wrapper" key={x.key}>
            <label className="custom-input-ctn">
            <input type="checkbox" onChange={(e)=> {e.persist(); onClick(e, content.key, x.key)}} checked={itemChecked} />
            <span className="checkmark"></span>
            <span className="search-sidebar-count-group">
              <span className="name">{x.label}</span>
              <span className="count">{count}</span>
            </span>
            </label>
          </div>
      );
    }
  });
  return (
    <React.Fragment>
    <div className="search-sidebar-accordion-wrapper">
      <div className="search-sidebar-accordion-title">
        <a href="#" aria-expanded={isOpen ? "true": "false"} onClick={toggleAccordion}>
        {content.label}
        </a>
      </div>
      { isOpen ?
      <div className="search-sidebar-accordion-content collapse in">
        {menuItems}
      </div>
    : null}
    </div>
    </React.Fragment>);
}

function SearchSidebar(props) {
  //console.log(props);
  let isOccurrence = false;
  let searchTypeLabel = '';
  if (props.searchType === 'dataset') {
    searchTypeLabel = '資料集';
  }
  else if (props.searchType === 'occurrence') {
    searchTypeLabel = '出現紀錄';
    isOccurrence = true;

    //const scientificNameContent = <SearchTaxon {...props.taxonProps} />;
    //searchTaxonContainer = <Accordion key="taxon" title="學名" content={scientificNameContent} appendClass="accordion-content-taxon" />;
    //searchTaxonContainer = <SearchTaxon {...props.taxonProps} />;
  }
  else if (props.searchType === 'species') {
    searchTypeLabel = '物種';
  }
  else if (props.searchType === 'publisher') {
    searchTypeLabel = '發布者';
  }
  let filterCount = 0;
  props.filters.forEach((item)=> {
    const key = item.split('=')[0];
    if (key !== 'offset') {
      filterCount++;
    }
  });
  /*
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
      <input className="form-control search-keyword" placeholder="搜尋關鍵字" name="search-term" id="search-term" type="text" value={props.queryKeyword} onChange={props.onChangeKeyword} onKeyPress={props.onKeyPressKeyword}/>
      <div className="input-group-btn">
      <button className="btn btn-default search-keyword-sign" type="submit" onClick={props.onClickSubmitKeyword}><i className="glyphicon glyphicon-search"></i></button>
      </div>
      </div>
      {searchTaxonContainer}
      {menuList}
      </div>)*/
  return (
      <div className="search-sidebar">
        <div className="modal right fade modal-search-side-wrapper" id="flowBtnModal" tabIndex="-1" role="dialog">
          <div className="modal-dialog" role="document">
            <div className="modal-content">
              <div className="search-sidebar-header">
                <span>{searchTypeLabel}</span>
                <div className="search-sidebar-header-del" data-toggle="tooltip" data-placement="left" title="清除" onClick={props.onClickClear}>
                  {filterCount > 0 ? <span className="badge">{filterCount}</span> : null}
                  <span className="glyphicon glyphicon-trash"></span>
                </div>
              </div>
              <div className="input-group search-sidebar-header-kw">
                <input className="form-control" placeholder="搜尋關鍵字" name="search-term" id="search-term" type="text" value="" value={props.queryKeyword} onChange={props.onChangeKeyword} onKeyPress={props.onKeyPressKeyword} />
                <div className="input-group-btn">
                  <button className="btn" type="submit" onClick={props.onClickSubmitKeyword}>
                    <i className="glyphicon glyphicon-search"></i>
                  </button>
                </div>
              </div>
              {isOccurrence === true ? <SearchTaxon {...props.taxonProps} />: null}

              {props.menus.map((m) => 
                (<Accordion key={m.key} content={m} onClick={props.onClick} filters={props.filters}/>)
               )}
            </div>
          </div>
        </div>
      </div>
  )
}

export default SearchSidebar;
