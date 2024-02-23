import React, {useState} from 'react';
//import Accordion from "./components/Accordion";
//import Tree from "./components/Tree";
import SearchTaxon from './SearchSidebarTaxon';
// import IconButton from '@material-ui/core/IconButton';
import {Delete} from '@material-ui/icons';
import Slider from '@material-ui/core/Slider';
import "./SearchKeyword.css";

import { Translation, useTranslation } from 'react-i18next';



function Accordion(props) {
  const {content, onClick, filters} = props;
  const [isOpen, setOpenState] = useState(false);
  const [filteredData, setFilteredData] = useState([]);
  const [taxonFiltedData, setTaxonFiltedData] = useState([]);

  let yearSelected = props.yearValue;
  filters.forEach((x) => {
    const [key, values] = x.split('=');
    if (key == 'year') {
      const vlist = values.split(',');
      yearSelected = [parseInt(vlist[0]), parseInt(vlist[1])];
    }
  });

  const long_term = new Set(['country',"taibif_county","dataset","publisher","highertaxon","rank"])
  let isLong = false;
  if (long_term.has(content.key)){
    isLong = true;
  }
  const sliderMarks = [];
  for (let i=1795; i<2024; i++) {
    sliderMarks.push({value: i, label: i});
  }

  const appendClass = (props.appendClass) ? ` ${props.appendClass}` : '';
  function toggleAccordion(e) {
    e.preventDefault()
    setOpenState(isOpen === false ? true : false);
  }

  const handleSliderCommitted = (event) => {
    onClick(event, content.key, props.yearValue.join(','))
  };
  const clearYearCondition = (event) => {
    props.clearCondition(event,content.key)
  };
  
  const datasetMenuItems = content.rows.map((x) => {
    if (content.key ===  'dataset'){   
      const count = (x.count) >=0 ? x.count.toLocaleString() : null;
      const itemChecked = filters.has(`${content.key}=${x.key}`);
      if (itemChecked){
        return (
            <div className="search-sidebar-checkbox-wrapper" key={x.key}>
              <label className="custom-input-ctn">
              <input type="checkbox" onChange={(e)=> {e.persist(); onClick(e, content.key, x.key)}} checked={itemChecked} />
              <span className="checkmark"></span>
              <span className="search-sidebar-count-group">
              <Translation>{t => <span className="name">{t(x.label)}</span>}</Translation>
                <span className="count">{count}</span>
              </span>
              </label>
            </div>
        );
      }
  }})
  const menuItems = content.rows.map((x) => {
    if(content.key ===  'year'){
      const handleChange = (event, newValue) => {
        setYearValue(newValue);
        onClick(event, content.key, newValue);
      };
    
      // console.log(content.key, handleChange)
      return (
          <div className="year_slider" key={x}>
          <Delete  style={{ position: 'absolute', right: 1 , width:'10%'}} onClick={clearYearCondition} />
          
          <Slider 
            style={{width:'90%',color: "#846C5B"}}
            value={props.yearValue}
            onChange={(e, newRange) => props.onSilderChange(newRange)}
            onChangeCommitted={handleSliderCommitted}
            max={props.defaultYearRange[1]}
            min={props.defaultYearRange[0]}
            valueLabelDisplay="auto"
            aria-labelledby="range-slider"
          />
          </div>
      );
    } else if (content.key ===  'dataset'){   
      const count = (x.count) >=0 ? x.count.toLocaleString() : null;
      const itemChecked = filters.has(`${content.key}=${x.key}`);
      if (!itemChecked){
        return (
            <div className="search-sidebar-checkbox-wrapper" key={x.key}>
              <label className="custom-input-ctn">
              <input type="checkbox" onChange={(e)=> {e.persist(); onClick(e, content.key, x.key)}} checked={itemChecked} />
              <span className="checkmark"></span>
              <span className="search-sidebar-count-group">
                <Translation>{t => <span className="name">{t(x.label)}</span>}</Translation>
                <span className="count">{count}</span>
              </span>
              </label>
            </div>
        );
      }
    } else if (content.key ===  'selfProduced'){   
      const count = (x.count) >=0 ? x.count.toLocaleString() : null;
      const itemChecked = filters.has(`${content.key}=${x.key}`);
      return (
          <div className="search-sidebar-checkbox-wrapper" key={x.key}>
            <label className="custom-input-ctn">
            <input type="checkbox" onChange={(e)=> {e.persist(); onClick(e, content.key, x.key)}} checked={itemChecked} />
            <span className="checkmark"></span>
            <span className="search-sidebar-count-group">
            <Translation>{t => <span className="name">{t(x.label == false ? 'GBIF' : 'TaiBIF IPT')}</span>}</Translation>
              <span className="count">{count}</span>
            </span>
            </label>
          </div>
      );
    } else {
      const count = (x.count) >=0 ? x.count.toLocaleString() : null;
      const itemChecked = filters.has(`${content.key}=${x.key}`);
      return (
          <div className="search-sidebar-checkbox-wrapper" key={x.key}>
            <label className="custom-input-ctn">
            <input type="checkbox" onChange={(e)=> {e.persist(); onClick(e, content.key, x.key)}} checked={itemChecked} />
            <span className="checkmark"></span>
            <span className="search-sidebar-count-group">
            <Translation>{t => <span className="name">{t(x.label)}</span>}</Translation>
              <span className="count">{count}</span>
            </span>
            </label>
          </div>
      );
    }
  });

  const handleFilter = (event) =>{
    const searchWord = event.target.value
    const newFilter = content.rows.filter((value)=>{
      return value.label.toLowerCase().includes(searchWord.toLowerCase())
    });

    if (searchWord ===""){
      setFilteredData([]);
    }else{
      setFilteredData(newFilter);
    }
  };
  
  const get_autocomplete_taxon = (event) =>{
    const searchWord = event.target.value
    const newFilter = content.rows.filter((value)=>{
      return value.label.toLowerCase().includes(searchWord.toLowerCase())
    });
    let apiUrl = null;

    apiUrl =  `${window.location.origin}/api/get_autocomplete_taxon/?keyword=${searchWord}`
    fetch(apiUrl)
    .then(res => res.json())
    .then(
      (jsonData) => {
        console.log('resp: ', jsonData);
        if (jsonData.solr_error_msg) {
          alert(jsonData.solr_error_msg); // TODO: need better UI
          return
        }
        if (searchWord ===""){
          setTaxonFiltedData([]);
        }else{
          setTaxonFiltedData(jsonData);
        }
      },
      (error) => {
      });
  };
  

  return (
    <React.Fragment>
    <div className="search-sidebar-accordion-wrapper">
      <div className="search-sidebar-accordion-title">
        <a href="#" aria-expanded={isOpen ? "true": "false"} onClick={toggleAccordion}>
        {content.label}
        </a>
      </div>
      { isOpen ?
      <div className={isLong ? "search-sidebar-accordion-content-scroll collapse in": "search-sidebar-accordion-content collapse in"}>
        {content.label == '資料集 Dataset'?
        <div className="searchInputs">
        <input type="text" placeholder="Search..." onChange={handleFilter} />
        </div>
        :null
        }
        {filteredData.length !=0 && (
        <div className="dataResult" style={{zIndex:'9999',position:'absolute'}} >
          {filteredData.slice(0,15).map((value, key) => {
            const itemChecked = filters.has(`${content.key}=${value.key}`);
            return (<div className="dataItem" key={key} onClick={(e)=> {e.persist(); onClick(e, content.key, value.key);}} >
               <p checked={!itemChecked}>{value.label}</p>
            </div>
          )})}
        </div>
        )}

        {content.label == '高階分類群 Higher Taxon Classification'? <div className="searchInputs"><input type="text" placeholder="Search..." onChange={get_autocomplete_taxon} /></div> : null }
        {taxonFiltedData.length !=0 && (
        <div className="dataResult" style={{zIndex:'9999',position:'absolute'}} >
          
          {taxonFiltedData.slice(0,15).map((value, key) => {
            const itemChecked = filters.has(`${content.key}=${value.key}`);
            return (<div className="dataItem" key={key} onClick={(e)=> {e.persist(); onClick(e, content.key, value.key);}} >
               <p checked={!itemChecked}>{value.label}</p>
            </div>
          )})}
        </div>
        )}
        {datasetMenuItems}
        {menuItems}
      </div>
    : null}
    </div>
    </React.Fragment>);
}

function SearchSidebar(props) {
  const currentYear = new Date().getFullYear();
  const defaultYearRange = [1795, currentYear];
  const [yearValue, setYearValue] = useState(defaultYearRange);

  const handleSilderOnChange = (newYearRange) => {
    setYearValue(newYearRange);
  }

  const handleCleanupOnClick = ()=> {
    setYearValue(defaultYearRange);
  }

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
      accordionList.push(<Accordion key={m.key} content={m} onClick={props.onClick} filters={props.filters} clearCondition={props.clearCondition} 
                                    defaultYearRange={ defaultYearRange } 
                                    yearValue={ yearValue }
                                    onSilderChange={ handleSilderOnChange }/>);
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
                <div className="search-sidebar-header-del" data-toggle="tooltip" data-placement="left" title="清除" onClick={() => {props.onClickClear(); handleCleanupOnClick()}}>
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

