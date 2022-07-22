import React, {useState, useRef} from 'react';
//import Accordion from "./components/Accordion";
//import Tree from "./components/Tree";
import SearchTaxon from './SearchSidebarTaxon';
// import IconButton from '@material-ui/core/IconButton';
// import DeleteIcon from '@material-ui/icons/Delete';
import Slider from '@material-ui/core/Slider';

function Accordion(props) {
  const {content, onClick, filters} = props;
  const [isOpen, setOpenState] = useState(false);
  const yearRange = [1900, 2021];// TODO: hard-coded
  let yearSelected = yearRange;
  filters.forEach((x) => {
    const [key, values] = x.split('=');
    if (key == 'year') {
      const vlist = values.split(',');
      yearSelected = [parseInt(vlist[0]), parseInt(vlist[1])];
    }
  });
  const [yearValue, setYearValue] = useState(yearSelected);

  const sliderMarks = [];
  for (let i=1900; i<2022; i++) {
    sliderMarks.push({value: i, label: i});
  }

  const appendClass = (props.appendClass) ? ` ${props.appendClass}` : '';
  function toggleAccordion(e) {
    e.preventDefault()
    setOpenState(isOpen === false ? true : false);
  }

  const handleSliderCommitted = (event) => {
    onClick(event, content.key, yearValue.join(','))
  };
  const clearYearCondition = (event) => {
    console.log(event, content.key)
    props.clearCondition(event,content.key)
  };
  const menuItems = content.rows.map((x) => {
    if(content.key ===  'year'){
      console.log(yearValue);
      const handleChange = (event, newValue) => {
        setYearValue(newValue);
        onClick(event, content.key, newValue);
      };
    
      // console.log(content.key, handleChange)
      return (
          <div className="year_slider" key={x}>
          <Slider
        value={yearValue}
        onChange={(e, newRange) => setYearValue(newRange)}
        onChangeCommitted={handleSliderCommitted}
        max={yearRange[1]}
        min={yearRange[0]}
        valueLabelDisplay="auto"
        aria-labelledby="range-slider"
          />
          </div>
      );
    } else{   
      const count = (x.count) >=0 ? x.count.toLocaleString() : null;
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
  const [queryKeyword, setQueryKeyword] = useState(props.queryKeyword);
  
  if (props.searchType === 'dataset') {
    if (props.language === 'zh-hant') {
      searchTypeLabel = '資料集';
    } else if (props.language === 'en'){
      searchTypeLabel = 'Dataset';
    }
  }
  else if (props.searchType === 'occurrence') {
    if (props.language === 'zh-hant') {
      searchTypeLabel = '出現紀錄';
    } else if (props.language === 'en'){
      searchTypeLabel = 'Occurrence';
    }
    
    isOccurrence = true;

    //const scientificNameContent = <SearchTaxon {...props.taxonProps} />;
    //searchTaxonContainer = <Accordion key="taxon" title="學名" content={scientificNameContent} appendClass="accordion-content-taxon" />;
    //searchTaxonContainer = <SearchTaxon {...props.taxonProps} />;
  }
  else if (props.searchType === 'species') {
    if (props.language === 'zh-hant') {
      searchTypeLabel = '物種';
    } else if (props.language === 'en'){
      searchTypeLabel = 'Species';
    }
    
  }
  else if (props.searchType === 'publisher') {
    if (props.language === 'zh-hant') {
      searchTypeLabel = '發布單位';
    } else if (props.language === 'en'){
      searchTypeLabel = 'Publisher';
    }
    
  }

  let filterCount = 0;
  let countMap = false;
  props.filters.forEach((item)=> {
    const key = item.split('=')[0];
    if (key !== 'offset' &&  key !== 'lat' &&  key !== 'lng') {
      filterCount++;
    }
    // map
    if ((key == 'lat' || key == 'lng' ) && !countMap){
      filterCount = filterCount +2;
      countMap = true;
    }
  });
  const handleChangeKeyword = (e) => {
    setQueryKeyword(e.target.value);
  }

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
  let accordionList = [];
  if (props.menus) {
    props.menus.forEach((m) => {
      accordionList.push(<Accordion key={m.key} content={m} onClick={props.onClick} filters={props.filters} clearCondition={props.clearCondition}/>);
    });
  }
  let formControlPlaceholder = '';
  if (props.language === 'zh-hant') {
    formControlPlaceholder = '搜尋關鍵字';
  } else if (props.language === 'en'){
    formControlPlaceholder = 'Keyword Search';
  }

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
      <input className="form-control" placeholder={formControlPlaceholder} name="search-term" id="search-term" type="text" value={queryKeyword} onChange={handleChangeKeyword} onKeyPress={props.onKeyPressKeyword} />
                <div className="input-group-btn">
      <button className="btn" type="submit" onClick={(e)=>props.onClickSubmitKeyword(e, queryKeyword)}>
                    <i className="glyphicon glyphicon-search"></i>
                  </button>
                </div>
              </div>
              {isOccurrence === true ? <SearchTaxon {...props.taxonProps} />: null}
              {accordionList}
            </div>
          </div>
        </div>
      </div>
  )
}

export default SearchSidebar;
