import React from 'react';
import SearchSidebar from './SearchSidebar.js';
import SearchMain from './SearchMain.js';
import './SearchStyles.css';
import {
  filtersToSearch,
} from './Utils'


class TaibifSearch extends React.Component {
  constructor(props) {
    super(props);

    let searchType = '';
    if (window.location.pathname === '/dataset/search/') {
      searchType = 'dataset';
    }
    else if (window.location.pathname === '/occurrence/search/' ||
             window.location.pathname === '/occurrence/taxonomy/' ||
             window.location.pathname === '/occurrence/map/' ||
             window.location.pathname === '/occurrence/gallery/' ||
             window.location.pathname === '/occurrence/charts/' ||
             window.location.pathname === '/occurrence/download/') {
      searchType = 'occurrence';
    }
    else if (window.location.pathname === '/publisher/search/') {
      searchType = 'publisher';
    }
    else if (window.location.pathname === '/species/search/') {
      searchType = 'species';
    }
    let language = document.getElementById('taibif-search-container').lang
 
    this.state = {
      isLoaded: false,
      isLoadedMain: true,
      search: {},
      menus: {},
      filters: new Set(),
      searchType: searchType,
      language: language,
      queryKeyword: '',
      taxonData: {
        suggestList: [],
        checked: {},
        tree: [],
        queryKeyword: '', // DEPRICATTED
      },
      //pagination: {},
      debounceTimeout: null,
    }
    this.handleMenuClick = this.handleMenuClick.bind(this);
    this.handleKeywordChange = this.handleKeywordChange.bind(this);
    this.handleKeywordEnter = this.handleKeywordEnter.bind(this);
    this.getSearch = this.getSearch.bind(this);
    this.handlePaginationClick = this.handlePaginationClick.bind(this);
    this.applyFilters = this.applyFilters.bind(this);
    this.handleSubmitKeywordClick = this.handleSubmitKeywordClick.bind(this);
    this.handleTabClick = this.handleTabClick.bind(this);

    this.handleTreeSpeciesClick = this.handleTreeSpeciesClick.bind(this);
    this.handleTaxonRemove = this.handleTaxonRemove.bind(this);
    this.handleTaxonKeywordChange = this.handleTaxonKeywordChange.bind(this);
    this.handleSuggestClick = this.handleSuggestClick.bind(this);
    this.debounce = this.debounce.bind(this);
    this.clearCondition = this.clearCondition.bind(this);
  }


  debounce(func, delay) {
    this.setState((prevState) => {
      let timeout = prevState.debounceTimeout;
      clearTimeout(timeout);
      timeout = setTimeout(func, delay);
      return {
        debounceTimeout: timeout,
      }
    });
  };

  handleTaxonKeywordChange(e) {
    const v = e.target.value;
    // TODO: debouncing
    const ele = document.querySelector('.search-taxon__suggest-list');
    if (v && ele) {
      ele.style.display = 'display';
    }

    this.setState((prevState) => {
      let taxonData = prevState.taxonData;
      taxonData.queryKeyword = v;
      return {
        taxonData: taxonData,
      }
    });

    const apiUrl = `/api/species/search/?q=${v}&rank=species`;
    fetch(apiUrl)
      .then(res => res.json())
      .then(
        (json) => {
          console.log('resp (key): ', json);
          this.setState((prevState) => {
            let taxonData = prevState.taxonData;
            if (json.search.results.length > 0) {
              taxonData.suggestList = json.search.results;
              return {
                taxonData: taxonData,
              }
            }
          });
        },
        (error) => {
        });
  }

  handleTreeSpeciesClick(e, tid, name, rank) {
    //e.stopPropagation();
    const filters = this.state.filters;
    let rankC = (rank) ? `${rank}:` : '';
    if (parseInt(tid) <= 6 && rankC == '') {
      rankC = 'kingdom:';
    }
    this.setState((prevState) => {
      const taxonData = prevState.taxonData;
      taxonData.checked[tid] = name;
      filters.add(`taxon_key=${rankC}${tid}`);
      return {
        isLoadedMain: false,
        taxonData: taxonData,
      }
    });
    this.applyFilters(filters);
  }

  handleTaxonRemove(e, tid) {
    const filters = this.state.filters;
    this.setState((prevState) => {
      const taxonData = prevState.taxonData;
      delete taxonData.checked[tid];
      const foundTaxonKeys = Array.from(filters).filter((x)=>x.indexOf('taxon_key=') >=0);

      foundTaxonKeys.forEach((x)=> {
        const klist = x.split('=');
        if (klist[1].indexOf(':') >= 0) {
          if (klist[1].split(':')[1] == tid) {
            filters.delete(x);
          }
        }
      });

      return {
        isLoadedMain: false,
        taxonData: taxonData,
      }
    });
    this.applyFilters(filters);
  }

  handleTabClick(e, core){
    const filters = this.state.filters;
    // only one core (tab)
    filters.forEach(function(x){
      if (x.indexOf('core=') >= 0) {
        filters.delete(x);
      }
    });
    if (core !== 'all') {
      filters.add(`core=${core}`);
    }
    this.applyFilters(filters);
  }

  handleSubmitKeywordClick(e, queryKeyword){
    const filters = this.state.filters;
    // only one queryKeyword
    if (queryKeyword != '') {
      filters.forEach(function(x){
        if (x.indexOf('q=') === 0) {
          filters.delete(x);
        }
      });
      filters.add(`q=${queryKeyword}`);
      this.applyFilters(filters);
    }
  }

  handleSuggestClick(e, speciesId, speciesName) {
    const ele = document.querySelector('.search-taxon__suggest-list');
    ele.style.display = 'none';

    const filters = this.state.filters;
    this.setState(prevState => {
      let taxonData = prevState.taxonData;
      taxonData.checked[speciesId] = speciesName;
      taxonData.queryKeyword = '';
      taxonData.suggestList = [];
      filters.add(`speciesId=${speciesId}`);
      return {
        taxonData: taxonData,
      }
    });
    this.applyFilters(filters);
  }


  handleKeywordChange(e) {
    const v = e.target.value;
    //this.setState({queryKeyword:v});
  }

  handleKeywordEnter(e) {
    if (e.charCode === 13){
      const v = e.target.value;
      this.handleSubmitKeywordClick(e, v);
    }
  }

  applyFilters(newFilters) {
    this.setState((state) => {
      if (newFilters) {
        this.getSearch(newFilters);
        return {filters: newFilters};
      }
      else {
        this.getSearch();
        return {
          queryKeyword: '',
          filters: new Set(),
        }
      }
    })
  }

  handleMenuClick(event, menuKey, itemKey) {
    this.setState({
      isLoadedMain: false,
    });
    const filters = this.state.filters;
    if (event.target.checked) {
      filters.add(`${menuKey}=${itemKey}`);
    }
    else {
      filters.delete(`${menuKey}=${itemKey}`);
    }

    if(menuKey == 'year') {
      filters.forEach(function(x){
        if (x.indexOf('year=') >= 0) {
          filters.delete(x);
        }
      });
      filters.add(`year=${itemKey}`);
    }

    this.applyFilters(filters);
  }

  clearCondition(event, menuKey) {

    this.setState({
      isLoadedMain: false,
    });
    const filters = this.state.filters;
      filters.forEach(function(x){
        if (x.indexOf('year=') >= 0) {
          filters.delete(x);
        }
      });
    this.applyFilters(filters);
  }

  /* DEPRICATED */
  handlePaginationClick(e, page) {
    let offset = this.state.search.offset;
    let limit = this.state.search.limit;
    const filters = this.state.filters;
    console.log(offset, limit, filters, 'page click');
  }

  getSearch(filters) {
    /* filters: Set() will affect API url and change current URL but not redirect */
    let pathname = window.location.pathname
    let apiUrl = null;
    let isOccurrence = false;
    let myRe = /\/occurrence\/.*/g;
    // let mapRe = /\/occurrence\/map/g; /* call map api when change to map tab */
    // if (mapRe.exec(pathname)){
    //   apiUrl = `${window.location.origin}/api/v2/occurrence/map`;
    //   isOccurrence = true;
    // }
    // else 
    if (myRe.exec(pathname)){
      apiUrl = `${window.location.origin}/api/v2/occurrence/search`;
      isOccurrence = true;
    }else{
      apiUrl = `${window.location.origin}/api${window.location.pathname}`;
    }
    
    // for window.history.pushState
    let url = `${window.location.origin}${window.location.pathname}`;
    /* TODO menu facet */
    const facetQueryString = (isOccurrence === true) ? 'facet=year&facet=month&facet=dataset&facet=dataset_id&facet=publisher&facet=country&facet=license&facet=taibif_county&facet=CoordinateInvalid&facet=TaxonMatchNone&facet=RecordedDateInvalid&facet=wildlife_refuges&facet=forest_reserves' : 'menu=1';
    if (filters) {
      let queryString = filtersToSearch(filters);
      apiUrl = `${apiUrl}?${queryString}&`;
      url = `${url}?${queryString}`;
    }
    else {
      apiUrl = `${apiUrl}?`;
    }
    apiUrl = `${apiUrl}${facetQueryString}`;

    window.history.pushState({stateObj:url}, "", url);

    console.log('fetch:', apiUrl)
    //const resp = await fetch(url);
    // const json = await resp.json();
    // async/await will cause: "regeneratorRuntime is not defined"
    // can sovle by babel setting
    fetch(apiUrl)
      .then(res => res.json())
      .then(
        (jsonData) => {
          console.log('resp: ', jsonData);
          if (jsonData.solr_error_msg) {
            alert(jsonData.solr_error_msg); // TODO: need better UI
            return
          }
          const results = isOccurrence ? jsonData.results : jsonData.search.results;
          const map_geojson = isOccurrence ? jsonData.map_geojson : '';
          const limit = isOccurrence ? jsonData.limit : jsonData.search.limit;
          const offset = isOccurrence ? jsonData.offset : jsonData.search.offset;
          const count = isOccurrence ? jsonData.count : jsonData.search.count;
          const elapsed = isOccurrence ? jsonData.elapsed : jsonData.search.elapsed;
          const taxonData = this.state.taxonData;
          taxonData.tree = jsonData.tree;
          if (!filters) {
            // clear checked taxon
            taxonData.checked = [];
          }
          console.log("json:",jsonData)
          this.setState({
            isLoaded: true,
            isLoadedMain: true,
            search: {
              results: results,
              map_geojson: map_geojson,
              limit: limit,
              offset: offset,
              count: count,
              elapsed: elapsed,
            },
            menus: jsonData.menus,
            taxonData:taxonData,
            serverError: jsonData.error,
          });
        },
        (error) => {
          this.setState({
            isLoaded: true,
            error
          });
        });
  }

  componentDidMount() {
    // handle if has query string
    if (window.location.search) {
      let filters = new Set();
      // decodeURI 對 %2C 沒作用?
      let mkeys = window.location.search.replace(/%2C/g,',').replace('?', '').split('&');
      let q = '';
      mkeys.forEach((m)=>{
        const mArr = m.split('=');
        if (mArr[0] === 'q') {
          //console.log(mArr[1]);
          filters.add(`q=${decodeURIComponent(mArr[1])}`);
          this.setState({queryKeyword:decodeURIComponent(mArr[1])});
        } else if (mArr[0] == 'taxon_key') {
          let taxonData = this.state.taxonData
          const kArr = m.split(':');
          const apiUrl = `/api/taxon/tree/node/${kArr[1]}`;
          fetch(apiUrl)
            .then(res => res.json())
            .then(
              (json) => {
                console.log('resp (tree): ', json);
                const speciesName = json.data.name;
                const tid = json.id;
                taxonData.checked[tid] = speciesName;
              },
              (error) => {
                console.log('cDidMount error tree', error);
              });
          filters.add(`${mArr[0]}=${mArr[1]}`);
          // console.log("aaa",mArr[1], this.state.taxonData);
          ///const taxonData = ta
        } else {
          filters.add(`${mArr[0]}=${mArr[1]}`);
        }
        //mArr[1].split(',').forEach((x) => {
        //  filters.add(`${mArr[0]}=${x}`);
        //})
        this.applyFilters(filters);
      });
    }
    else {
      this.getSearch();
    }
  }

  render() {
    const { error, isLoaded, search, menus, serverError, isLoadedMain } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div className="search-loading"> 🌱 Loading... ⏳ </div>
    }  else if (serverError) {
      return `[server]: ${serverError}`; // should not shou this on production
    }
    else {
      //console.log('state: ', this.state);
      const menus = this.state.menus;
      const filters = this.state.filters;
      const searchType = this.state.searchType;
      const language = this.state.language;
      const mainData = this.state.search;
      const queryKeyword = this.state.queryKeyword; // DEPRICATTED

      const taxonProps = {
        taxonData: this.state.taxonData,
        onTreeSpeciesClick: this.handleTreeSpeciesClick,
        onTaxonRemoveClick: this.handleTaxonRemove,
        onTaxonKeywordChange: this.handleTaxonKeywordChange,
        onSuggestClick: this.handleSuggestClick,
      };

      let searchMainContainer = '';
      if (!isLoadedMain) {
        // via: https://codepen.io/kingfisher13/pen/vKXwNN
        searchMainContainer = (
            <div className="col-xs-12 col-md-9">
            <div className="container">
            <div className="loader">
            <div className="loader-wheel"></div>
            <div className="loader-text"></div>
            </div>
            </div>
            </div>
        );
      } else {
        searchMainContainer = <SearchMain data={mainData} searchType={searchType} language={language} filters={filters} menus={menus} onClickTab={this.handleTabClick} taxonProps={taxonProps} />;
      }

      const defaultPage = (this.state.page) ? this.state.page : '1';

      return (
          <div className="row">
            <div className="visible-xs">
              <a href="#" className="xs-schedule-flow-btn myicon icon-filter" data-toggle="modal" data-target="#flowBtnModal">進階篩選</a>
            </div>
            <SearchSidebar menus={menus} onClick={this.handleMenuClick} filters={filters} onClickClear={(e)=>this.applyFilters()} queryKeyword={queryKeyword} onChangeKeyword={(e)=>{this.handleKeywordChange(e)}} onKeyPressKeyword={(e)=>{this.handleKeywordEnter(e)}} onClickSubmitKeyword={this.handleSubmitKeywordClick} searchType={searchType} language={language} taxonProps={taxonProps} clearCondition={this.clearCondition} />
          {searchMainContainer}
          </div>
      );
    }
  }
}

export default TaibifSearch;
