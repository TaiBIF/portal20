import React from 'react';
import SearchSidebar from './SearchSidebar.js';
import SearchMain from './SearchMain.js';
import './SearchStyles.css';


function filtersToQuerystring (filters) {
  //TODO: Array.from(filters).join('&');
  const qsArr = [];
  filters.forEach((item)=> {
    qsArr.push(item);
  });
  return qsArr.join('&');
}

function Pagination (props) {
  const {count, limit, offset} = props.data;
  //const lastPage = hasCount ? Math.ceil(count / numPerPage) : parseInt(current)+1;
  //console.log(numPerPage, hasCount, 'pag');
  const currentPage = Math.ceil(offset / limit) + 1;
  const lastPage = Math.ceil(count / limit);

  let pageElements = [];

  function _createPage(i) {
    pageElements.push(<li key={i} className={(i==currentPage) ? 'active' : null}><a href="#" onClick={(e)=>props.onClick(e, i)}>{i}</a></li>);
  }

  if (lastPage <= 10 ) {
    for (let i=1; i<=lastPage;i++) {
      _createPage(i);
    }
  } else {
    if (currentPage >= 4 ) {
      pageElements.push(<li key="pre-dot"><a>...</a></li>);
    }
    for (let i=1; i<=lastPage;i++) {
      if ( currentPage == i || currentPage - 1 == i || currentPage + 1 == i ) {
        _createPage(i);
      }
    }
    if (currentPage <= lastPage - 2 ) {
      pageElements.push(<li key="post-dot"><a>...</a></li>);
    }
  }

  return (
      <div className="center-block text-center">
        <ul className="pagination">
          <li>
            <a href="#" aria-label="Previous" onClick={(e)=>props.onClick(e, 1)}>
            <span aria-hidden="true">&laquo;</span>
            </a>
          </li>
          {pageElements}
          <li>
            <a href="#" aria-label="Next" onClick={(e)=>props.onClick(e, lastPage)}>
              <span aria-hidden="true">&raquo;</span>
            </a>
          </li>
         </ul>
      </div>
  );
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
      taxonData: {
        suggestList: [],
        checked: {},
        tree: [],
        queryKeyword: '',
      },
      pagination: {},
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

  handleTreeSpeciesClick(e, tid, name) {
    const filters = this.state.filters;
    this.setState((prevState) => {
      const taxonData = prevState.taxonData;
      taxonData.checked[tid] = name;
      filters.add(`taxon_key=${tid}`);
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
      filters.delete(`taxon_key=${tid}`);
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
    this.setState({queryKeyword:v});
  }

  handleKeywordEnter(e) {
    if (e.charCode === 13){
      const v = e.target.value;
      this.handleSubmitKeywordClick();
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
    this.applyFilters(filters);
  }

  handlePaginationClick(e, page) {
    let offset = this.state.search.offset;
    let limit = this.state.search.limit;
    const filters = this.state.filters;

    offset = (page-1) * limit;
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
        (jsonData) => {
          console.log('resp: ', jsonData);
          const taxonData = this.state.taxonData;
          taxonData.tree = jsonData.tree;
          this.setState({
            isLoaded: true,
            isLoadedMain: true,
            search: jsonData.search,
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
      return <div className="search-loading"> 🌱 Loading... ⏳ </div>
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
      } else {
        const pagination = <Pagination onClick={this.handlePaginationClick} data={mainData}/>;
        searchMainContainer = <SearchMain data={mainData} searchType={searchType} filters={filters} menus={menus} onClickTab={this.handleTabClick} pagination={pagination} />;
      }

      const defaultPage = (this.state.page) ? this.state.page : '1';
      const taxonProps = {
        taxonData: this.state.taxonData,
        onTreeSpeciesClick: this.handleTreeSpeciesClick,
        onTaxonRemoveClick: this.handleTaxonRemove,
        onTaxonKeywordChange: this.handleTaxonKeywordChange,
        onSuggestClick: this.handleSuggestClick,
      };
        /*<SearchSidebar menus={menus} onClick={this.handleMenuClick} filters={filters} onClickClear={(e)=>this.applyFilters()} queryKeyword={queryKeyword} onChangeKeyword={(e)=>{this.handleKeywordChange(e)}} onKeyPressKeyword={(e)=>{this.handleKeywordEnter(e)}} onClickSubmitKeyword={this.handleSubmitKeywordClick} searchType={searchType} taxonProps={taxonProps} />

          */
      return (
          <div className="row">
            <div className="visible-xs">
              <a href="#" className="xs-schedule-flow-btn myicon icon-filter" data-toggle="modal" data-target="#flowBtnModal">進階篩選</a>
            </div>
            <SearchSidebar menus={menus} onClick={this.handleMenuClick} filters={filters} onClickClear={(e)=>this.applyFilters()} queryKeyword={queryKeyword} onChangeKeyword={(e)=>{this.handleKeywordChange(e)}} onKeyPressKeyword={(e)=>{this.handleKeywordEnter(e)}} onClickSubmitKeyword={this.handleSubmitKeywordClick} searchType={searchType} taxonProps={taxonProps} />
          {searchMainContainer}
          </div>
      );
    }
  }
}

export default TaibifSearch;
