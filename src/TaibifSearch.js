import React from 'react';
import SearchSidebar from './SearchSidebar.js';
import {SearchMainDataset, SearchMainOccurrence, SearchMainPublisher, SearchMainSpecies} from './SearchMain.js';
import './SearchStyles.css';


function filtersToQuerystring (filters) {
  const qsArr = [];
  filters.forEach((item)=> {
    qsArr.push(item);
  });
  return qsArr.join('&');
}

function Pagination (props) {
  const hasCount = parseInt(props.count) ? true : false;
  const numPerPage = props.limit - props.offset;
  const lastPage = hasCount ? Math.ceil(props.count / numPerPage) : parseInt(props.current)+1;

  return (
      <div className="center-block text-center">
      <div className="btn-group" role="group" aria-label="...">
      <button type="button" className="btn btn-default" onClick={(e)=>props.onClick(e, 'prev')}>上一頁</button>
      <button type="button" className="btn btn-default" onClick={(e)=>props.onClick(e, 'next')}>下一頁</button>
      </div>
      </div>
  )
}

class TaibifSearch extends React.Component {
  constructor(props) {
    super(props);

    let searchType = '';
    if (window.location.pathname === '/dataset/search/') {
      searchType = 'dataset';
    }
    else if (window.location.pathname === '/occurrence/search/') {
      searchType = 'occurrence';
    }
    else if (window.location.pathname === '/publisher/search/') {
      searchType = 'publisher';
    }
    else if (window.location.pathname === '/species/search/') {
      searchType = 'species';
    }

    this.state = {
      isLoaded: false,
      isLoadedMain: true,
      search: {},
      menus: {},
      filters: new Set(),
      searchType: searchType,
      queryKeyword: '',
      pagination: {},
    }
    this.handleMenuClick = this.handleMenuClick.bind(this);
    this.handleKeywordChange = this.handleKeywordChange.bind(this);
    this.getSearch = this.getSearch.bind(this);
    this.handlePaginationClick = this.handlePaginationClick.bind(this);
    this.applyFilters = this.applyFilters.bind(this);
    this.handleSubmitKeywordClick = this.handleSubmitKeywordClick.bind(this);
    this.handleTabClick = this.handleTabClick.bind(this);
  }

  handleTabClick(e, core){
    const filters = this.state.filters;
    // only one core (tab)
    filters.forEach(function(x){
      if (x.indexOf('core.') === 0) {
        filters.delete(x);
      }
    });
    if (core !== 'all') {
      filters.add(`core.${core}`);

    this.applyFilters(filters);
    }
  }

  handleSubmitKeywordClick(){
    const filters = this.state.filters;
    const q = this.state.queryKeyword;
    // only one queryKeyword
    filters.forEach(function(x){
      if (x.indexOf('q=') === 0) {
        filters.delete(x);
      }
    });
    filters.add(`q=${q}`);
    this.applyFilters(filters);
  }

  handleKeywordChange(e) {
    const v = e.target.value;
    this.setState({queryKeyword:v});
  }

  applyFilters(newFilters) {
    this.setState((state) => {
      if (newFilters) {
        this.getSearch(newFilters);
        return {filters: newFilters};
      }
      else {
        this.getSearch();
        return {filters: new Set(),
                queryKeyword:''}
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
    this.applyFilters(filters);
  }

  handlePaginationClick(e, cat) {
    let offset = this.state.search.offset;
    let limit = this.state.search.limit;
    const filters = this.state.filters;
    offset = (cat === 'next') ? offset + limit : offset - limit;
    offset = Math.max(0, offset);
    const pageParam = `offset=${offset}&limit=${limit}`;
    let pageApiUrl = `${window.location.origin}/api${window.location.pathname}`;
    if (filters) {
      let queryString = filtersToQuerystring(filters);
      pageApiUrl = `${pageApiUrl}?${queryString}&${pageParam}`;
    }
    else {
      pageApiUrl = `${apiUrl}?${pageParam}`;
    }
    this.setState({
      isLoadedMain: false,
    });
    console.log('fetch (page):', pageApiUrl);
    fetch(pageApiUrl)
      .then(res => res.json())
      .then(
        (json) => {
          console.log('resp (page): ', json);
          this.setState({
            isLoadedMain: true,
              search: json.search,
              serverError: json.error
          });
        },
        (error) => {
          this.setState({
            isLoaded: true,
            error
          });
        });
  }

  getSearch(filters) {
    /* filters: Set() will affect API url and change current URL but not redirect */
    let apiUrl = `${window.location.origin}/api${window.location.pathname}`;
    // for window.history.pushState
    let url = `${window.location.origin}${window.location.pathname}`;

    if (filters) {
      let queryString = filtersToQuerystring(filters);
      apiUrl = `${apiUrl}?${queryString}&menu=1`;
      url = `${url}?${queryString}`;
    }
    else {
      apiUrl = `${apiUrl}?menu=1`;
    }

    window.history.pushState({stateObj:url}, "", url);

    console.log('fetch:', apiUrl)
    //const resp = await fetch(url);
    // const json = await resp.json();
    // async/await will cause: "regeneratorRuntime is not defined"
    // can sovle by babel setting
    fetch(apiUrl)
      .then(res => res.json())
      .then(
        (json) => {
          console.log('resp: ', json);
          const data = json.data;
          this.setState({
            isLoaded: true,
            isLoadedMain: true,
            search: json.search,
            menus: json.menus,
            serverError: json.error,
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
          this.setState({queryKeyword:decodeURIComponent(mArr[1])});
        }
        mArr[1].split(',').forEach((x) => {
          filters.add(`${mArr[0]}=${x}`);
        })
      });
      this.applyFilters(filters);
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
      return <div className="search-loading"> 🌱 Searching... ⏳ </div>
    }  else if (serverError) {
      return `[server]: ${serverError}`; // should not shou this on production
    }
    else {
      //console.log('state: ', this.state);
      const menus = this.state.menus;
      const filters = this.state.filters;
      const searchType = this.state.searchType;
      const mainData = this.state.search;
      const queryKeyword = this.state.queryKeyword;
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
      }
      else if (searchType === 'dataset') {
        searchMainContainer = <SearchMainDataset data={mainData} searchType={searchType} filters={filters} menus={menus} onClickTab={this.handleTabClick}/>
      }
      else if (searchType === 'occurrence') {
          searchMainContainer = <SearchMainOccurrence data={mainData} searchType={searchType} filters={filters} menus={menus} />
      }
      else if (searchType === 'publisher') {
        searchMainContainer = <SearchMainPublisher data={mainData} searchType={searchType} filters={filters} menus={menus} />
      }
      else if (searchType === 'species') {
        searchMainContainer = <SearchMainSpecies data={mainData} searchType={searchType} filters={filters} menus={menus} />
      }

      const defaultPage = (this.state.page) ? this.state.page : '1';
      return (
          <div className="row">
          <SearchSidebar menus={menus} onClick={this.handleMenuClick} filters={filters} onClickClear={(e)=>this.applyFilters()} queryKeyword={queryKeyword} onChangeKeyword={(e)=>{this.handleKeywordChange(e)}} onClickSubmitKeyword={this.handleSubmitKeywordClick} searchType={searchType} />
          {searchMainContainer}
          <Pagination onClick={this.handlePaginationClick} />
          </div>
      );
    }
  }
}

export default TaibifSearch;
