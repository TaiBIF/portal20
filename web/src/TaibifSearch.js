import React from 'react';
import SearchSidebar from './SearchSidebar.js';
import SearchMain from './SearchMain.js';
import './SearchStyles.css';

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

    this.state = {
      isLoaded: false,
      data: {},
      filters: new Set(),
      searchType: searchType,
      queryKeyword: ''
    }
    this.handleMenuClick = this.handleMenuClick.bind(this);
    this.handleKeywordChange = this.handleKeywordChange.bind(this);
    this.getSearch = this.getSearch.bind(this);
    this.applyFilters = this.applyFilters.bind(this);
    this.handleSubmitKeywordClick = this.handleSubmitKeywordClick.bind(this);
  }
  handleSubmitKeywordClick(){
    const filters = this.state.filters;
    const q = this.state.queryKeyword;
    // only one queryKeyword
    filters.forEach(function(x){
      if (x.indexOf('q.') === 0) {
        filters.delete(x);
      }
    });
    filters.add(`q.${q}`);
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
    const filters = this.state.filters;
    if (event.target.checked) {
      filters.add(`${menuKey}.${itemKey}`);
    }
    else {
      filters.delete(`${menuKey}.${itemKey}`);
    }
    this.applyFilters(filters);
  }

  getSearch(filters) {
    /* filters: Set() will affect API url and change current URL but not redirect */
    let apiUrl = `${window.location.origin}/api${window.location.pathname}`;
    let url = `${window.location.origin}${window.location.pathname}`;
    // convert Set to object
    if (filters) {
      const obj = {};
      filters.forEach((item)=> {
        const k = item.split('.');
        if (obj.hasOwnProperty(k[0])) {
          obj[k[0]].push(k[1]);
        }
        else {
          obj[k[0]] = [k[1]];
        }
      });
      const queryString = new URLSearchParams(obj).toString();
      apiUrl = `${apiUrl}?${queryString}`;
      url = `${url}?${queryString}`;
    }
    // do not redirect
    window.history.pushState("object or string", "taibif-search", url);
  
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
          this.setState({
            isLoaded: true,
            data: json.data,
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
          this.setState({queryKeyword:mArr[1]});
        }
        mArr[1].split(',').forEach((x) => {
          filters.add(`${mArr[0]}.${x}`);
        })
      });

      this.applyFilters(filters);
    }
    else {
      this.getSearch();
    }

  }

  render() {
    const { error, isLoaded, data, serverError } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div className="search-loading"> 🌱 Loading... ⏳ </div>
    }  else if (serverError) {
      return `[server]: ${serverError}`; // should not shou this on production
    }
    else {
      //console.log('state: ', this.state);
      const menus = this.state.data.menus;
      const filters = this.state.filters;
      const searchType = this.state.searchType;
      const mainData = {
        'results': this.state.data.results,
        'count':  this.state.data.count,
        'limit':  this.state.data.limit,
        'offset':  this.state.data.offset
      };
      const queryKeyword = this.state.queryKeyword;
      return (<div className="row">
              <SearchSidebar menus={menus} onClick={this.handleMenuClick} filters={filters} onClickClear={(e)=>this.applyFilters()} queryKeyword={queryKeyword} onChangeKeyword={(e)=>{this.handleKeywordChange(e)}} onClickSubmitKeyword={this.handleSubmitKeywordClick} searchType={searchType} />
              <SearchMain data={mainData} searchType={searchType} />
              </div>);
    }
  }
}

export default TaibifSearch;
