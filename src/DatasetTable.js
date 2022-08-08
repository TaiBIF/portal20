import React from 'react';

class DatasetTable extends React.Component {
  constructor(props) {
    super(props);

    let language = document.getElementById('dataset-table-container').lang

    this.state = {
      isLoaded: false,
      filters: new Set(),
      sortDirection: 1,
      sortKey: '',
      language: language,
    }
    this.applyFilters = this.applyFilters.bind(this);
    this.handlePaginate = this.handlePaginate.bind(this);
    this.handleSort = this.handleSort.bind(this);
  }
  
  handleSort(e, key) {
    let filters = this.state.filters;
    let sort = this.state.sortDirection;
    for (let i of filters) {
      if (i.indexOf('order_by=') >= 0) {
        filters.delete(i);
        break;
      }
    }
    if (sort  === 1) {
      filters.add(`order_by=-${key}`);
    }
    else {
      filters.add(`order_by=${key}`);
    }

    // reset offset
    for (let i of filters) {
      if (i.indexOf('offset=') >= 0) {
        filters.delete(i);
        break;
      }
    }
    filters.add('offset=0');

    this.setState({
      isLoaded: false,
      sortDirection: sort * -1,
      sortKey: key,
    });
    this.applyFilters(filters);
  }

  handlePaginate(e, cat='', disabled=''){
    e.preventDefault();
    if (disabled) {
      return false;
    }
    let filters = this.state.filters;
    const limit = this.state.data.limit;
    const offset = (cat == 'next') ?
          this.state.data.offset + limit :
          this.state.data.offset - limit;
    for (let i of filters) {
      if (i.indexOf('offset=') >= 0) {
        filters.delete(i);
        break;
      }
    }
    filters.add(`offset=${offset}`);
    this.setState({
      isLoaded: false,
    });
    this.applyFilters(filters);
  }

  handlePaginate2(e, cat='', disabled=''){
    e.preventDefault();
    if (disabled) {
      return false;
    }
    let filters = this.state.filters;
    const limit = this.state.data.limit;
    const offset = (cat-1)* limit;
    for (let i of filters) {
      if (i.indexOf('offset=') >= 0) {
        filters.delete(i);
        break;
      }
    }
    filters.add(`offset=${offset}`);
    this.setState({
      isLoaded: false,
    });
    this.applyFilters(filters);
  }

  applyFilters(filters) {
    const queryString = (filters) ?
          Array.from(filters).join('&') :
          '';
    const apiUrl = (queryString === '') ?
          '/api/dataset/search' :
          `/api/dataset/search?${queryString}`;

    // console.log('fetch: ', apiUrl);
    fetch(apiUrl)
      .then(res => res.json())
      .then(
        (jsonData) => {
          console.log('resp: ', jsonData);
          this.setState({
            isLoaded: true,
            data: jsonData.search,
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
    const qs = window.location.search;
    let filters = this.state.filters;
    if (qs.indexOf('most=1')>=0) {
      filters.add('is_most_project=1');
      this.applyFilters(filters);
    }
    else {
      this.applyFilters();
    }
  }

  render() {
    const { error, isLoaded, data, serverError,language } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div className="search-loading"> Loading... ⏳ </div>
    }  else if (serverError) {
      return `[server]: ${serverError}`; // should not shou this on production
    }
    else {
      const dataList = data.results.map((v, i)=>{
        const dtime = v.pub_date.replace(/-/g, '/');
        const num_record = v.num_record.toLocaleString();
        const num_occurrence = v.num_occurrence.toLocaleString();
        let pubMemo = '';
        if (v.status === 'PUBLIC') {
          if (language === 'en') {
            pubMemo = (v.guid) ? 'Registered to GBIF' : 'Not registered to GBIF';
          }
          else { 
            pubMemo = (v.guid) ? '已註冊至 GBIF' : '未註冊至 GBIF';
          }
          pubMemo = <div><small>{pubMemo}</small></div>;
        }
        
        const title = (v.status === 'PUBLIC') ? <a href={"/dataset/"+v.name}>{v.title}</a>:v.title;

        return (<tr key={i}>
                <td>{data.offset+i+1}</td>
                <td>{title}</td>
                <td>{v.publisher}</td>
                <td>{v.dwc_type}</td>
                <td>{num_record}</td>
                <td>{num_occurrence}</td>
                <td>{dtime}</td>
                <td>{v.country}</td>
                <td>{v.status_display}{pubMemo}</td>
                </tr>)
      })
      const currentPageNum = Math.ceil(data.offset / data.limit) + 1;
      let paginationList = []
      for (let i = 1; i <= (Math.ceil(data.count/data.limit)); i++) {
        let disabledPage = (currentPageNum === i) ? ' disabled' : '';
        paginationList.push(<li className={"page" + disabledPage} key={i} ><a style={{'margin': '10px'}} href="#" onClick={(e)=>this.handlePaginate2(e, i, disabledPage )}>{i}</a></li>)
      }

      const disabledPrev = (data.offset === 0) ? ' disabled' : '';
      const disabledNext = (data.has_more === false) ? ' disabled' : '';
      const tableColName = (language === 'en') ? [
        ['title', 'Dataset name'],
        ['organization', 'Publisher'],
        ['dwc_core_type', 'Data type'],
        ['num_record','Data count'],
        ['num_occurrence', 'Occurrence'],
        ['pub_date', 'Publish time'],
        ['country', 'Area'],
        ['status', 'Open status'],
      ] : [
        ['title', '資料集名稱'],
        ['organization', '發布單位'],
        ['dwc_core_type', '資料類型'],
        ['num_record','資料筆數'],
        ['num_occurrence', '出現紀錄'],
        ['pub_date', '發佈時間'],
        ['country', '地區'],
        ['status', '公開狀態'],
      ];
      const theadItems = tableColName.map((v, i) => {
        let finger = null;
        if (this.state.sortDirection != null && this.state.sortKey === v[0]) {
          finger = (this.state.sortDirection > 0) ? '👇' : '👆';
        }
        return <th style={{'cursor': 'pointer'}} key={i} onClick={(e)=>this.handleSort(e, v[0])}>{v[1]}{finger}</th>
      });
      //
      return (
          <div>
            {(language ==='en')? <h3>List of dataset <small><a href="/dataset/search" className="btn btn-default"> 👉 Search dataset</a></small></h3>
            :<h3>資料集列表 <small><a href="/dataset/search" className="btn btn-default"> 👉 搜尋資料集</a></small></h3>}
          <table className="table table-bordered">
          <colgroup>
          <col span="1" style={{'width': '2%'}}/>
          <col span="1" style={{'width': '15%'}}/>
          <col span="1" style={{'width': '13%'}}/>
          <col span="1" style={{'width': '15%'}}/>
          <col span="1" style={{'width': '10%'}}/>
          <col span="1" style={{'width': '10%'}}/>
          <col span="1" style={{'width': '10%'}}/>
          <col span="1" style={{'width': '10%'}}/>
          <col span="1" style={{'width': '15%'}}/>
          </colgroup>
          <thead>
          <tr>
          <th>#</th>
          {theadItems}
          </tr>
          </thead>
          <tbody>
          {dataList}
          </tbody>
          </table>
          <nav aria-label="...">
          <ul className="pager">
          {paginationList}

          </ul>
          </nav>
          </div>
      )
    }
  }
}

export default DatasetTable;
