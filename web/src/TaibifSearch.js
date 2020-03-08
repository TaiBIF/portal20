import React from 'react';
import SearchSidebar from './SearchSidebar.js';
import {SearchMainDataset, SearchMainOccurrence, SearchMainPublisher} from './SearchMain.js';
import './SearchStyles.css';


function Pagination (props) {
  const hasCount = parseInt(props.count) ? true : false;
  const numPerPage = props.limit - props.offset;
  const lastPage = hasCount ? Math.ceil(props.count / numPerPage) : parseInt(props.current)+1;
  const pages = [];
  for (let i=1; i<=lastPage; i++)  {
    let url = window.location.href;
    if (url.indexOf('page=') >=0) {
      url = url.replace(/page=([0-9]+)/, `page=${i}`);
    }
    else {
      if (window.location.search) {
        url = `${url}&page=${i}`;
      }
      else {
        url = `${url}?page=${i}`;
      }
    }
    const activeClass = (parseInt(props.current, 10) === i) ? 'active' : '';
    if (hasCount) {
      pages.push(<li className={activeClass} key={i}><a href={url}> {i} </a></li>);
    }
  }
  return (
      <div className="center-block text-center">
      <ul className="pagination">
      <li><a href="?page=1" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>
      {pages}
      <li><a href={"?page="+lastPage} aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>
      </ul>
      </div>
  )
}

class TaibifSearch extends React.Component {
  constructor(props) {
    super(props);

    let searchType = '';
    let page = 0;
    if (window.location.pathname === '/dataset/search/') {
      searchType = 'dataset';
    }
    else if (window.location.pathname === '/occurrence/search/') {
      searchType = 'occurrence';
    }
    else if (window.location.pathname === '/publisher/search/') {
      searchType = 'publisher';
    }

    if (window.location.search.indexOf('page=')) {
      let found = window.location.search.split('&').find((x)=>x.indexOf('page=') >=0)
      if (found) {
        page = found.split('=')[1]
      }
    }
    this.state = {
      isLoaded: false,
      data: {},
      filters: new Set(),
      searchType: searchType,
      queryKeyword: '',
      page: page
    }
    this.handleMenuClick = this.handleMenuClick.bind(this);
    this.handleKeywordChange = this.handleKeywordChange.bind(this);
    this.getSearch = this.getSearch.bind(this);
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
      let queryString = new URLSearchParams(obj).toString();
      queryString = decodeURIComponent(queryString);
      apiUrl = `${apiUrl}?${queryString}`;
      url = `${url}?${queryString}`;
    }

    // if has page, redirect occur ?
    if (this.state.page) {
      if (filters) {
        apiUrl = `${apiUrl}&page=${this.state.page}`;
      }
      else {
        apiUrl = `${apiUrl}?page=${this.state.page}`;
      }
    }
    else {
      //有 page 的話, 會rudirect 變成拿掉 page
      //window.history.pushState("object or string", "taibif-search", url);
    }
    ///apiUrl = '';
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
        if (m.indexOf('page=') < 0) {
          const mArr = m.split('=');
          if (mArr[0] === 'q') {
            console.log(mArr[1]);
            this.setState({queryKeyword:decodeURIComponent(mArr[1])});
          }
          mArr[1].split(',').forEach((x) => {
            filters.add(`${mArr[0]}.${x}`);
          })
        }
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
      return <div className="search-loading"> 🌱 Searching... ⏳ </div>
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
      let searchMainContainer = '';
      if (searchType === 'dataset') {
        searchMainContainer = <SearchMainDataset data={mainData} searchType={searchType} filters={filters} menus={menus} onClickTab={this.handleTabClick}/>
      }
      else if (searchType === 'occurrence') {
        searchMainContainer = <SearchMainOccurrence data={mainData} searchType={searchType} filters={filters} menus={menus} />
      }
      else if (searchType === 'publisher') {
        searchMainContainer = <SearchMainPublisher data={mainData} searchType={searchType} filters={filters} menus={menus} />
      }

      const defaultPage = (this.state.page) ? this.state.page : '1';
      return (
          <div className="row">
          <SearchSidebar menus={menus} onClick={this.handleMenuClick} filters={filters} onClickClear={(e)=>this.applyFilters()} queryKeyword={queryKeyword} onChangeKeyword={(e)=>{this.handleKeywordChange(e)}} onClickSubmitKeyword={this.handleSubmitKeywordClick} searchType={searchType} />
          {searchMainContainer}
          <Pagination limit={mainData.limit} offset={mainData.offset} count={mainData.count} current={defaultPage } />
          </div>
      );
    }
  }
}

export default TaibifSearch;
