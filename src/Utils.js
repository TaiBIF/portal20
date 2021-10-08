import React from 'react';

async function fetchData(url) {
  if(/^year=/.test(url))
    url = url.replace("-",",")

  //console.log('🙋', url);
  let response = await fetch(url);
  let data = await response.json();
  console.log( '🚍', data);
  return data;
}

const filtersToSearch = (filters, removeOffset=false) => {
  //TODO: Array.from(filters).join('&');
  //console.log(removeOffset);
  const qsArr = [];
  filters.forEach((item)=> {
    if(/^year=/.test(item))
      item = item.replace("-",",")

    if (/^offset=/.test(item)) {
      if (removeOffset === false) {
        qsArr.push(item);
      }
    } else {
      qsArr.push(item);
    }
  });
  return qsArr.join('&');
}

const appendUrl = (url, queryString) => {
  if (url.indexOf('?') >= 0) {
    return `${url}&${queryString}`;
  } else {
    return `${url}?${queryString}`;
  }
}
const Pagination = ({total, offset=0, urlPrefix}) => {
  // fixed
  const limit = 20;
  const numPageDisplay = 5
  const offsetLimit = limit * numPageDisplay;
  // count
  const currentPage = Math.ceil(offset / limit) + 1;
  const lastPage = Math.ceil(total / limit);
  const stepLimit = Math.min(lastPage, numPageDisplay);

  const pageStart = (Math.floor(offset/offsetLimit) * numPageDisplay) + 1;
  let step = 0;
  const offsetStart = Math.floor(offset/offsetLimit) * offsetLimit;
  let pageOffset = offsetStart;
  const pageList = [];
  while (step < stepLimit && pageOffset < total) {
    const url = appendUrl(urlPrefix, `offset=${pageOffset}`);
    pageList.push(<li key={urlPrefix+step} className={(offset === pageOffset) ? 'active' : null}><a href={url}>{step+pageStart}</a></li>);
    step++;
    pageOffset += limit;
  }

  return (
      <div className="center-block text-center">
      <ul className="pagination">
      <li>
      <a href={urlPrefix} aria-label="Previous">
      <span aria-hidden="true">&laquo;</span>
      </a>
      </li>
      { (offsetStart - limit >= 0) ?
        <li><a href={appendUrl(urlPrefix, `offset=${offsetStart-limit}`)}>...</a></li>
        : null}
      {pageList}
      { (pageOffset + limit < total) ?
        <li><a href={appendUrl(urlPrefix, `offset=${offsetStart+limit}`)}>...</a></li>
        : null}
      <li>
      { (pageOffset + limit < total ) ?
        <a href={appendUrl(urlPrefix, `offset=${pageOffset+limit}`)}  aria-label="Next">
        <span aria-hidden="true">&raquo;</span>
        </a>
        : null
      }
      </li>
      </ul>
      </div>
  );
}


const Pagination2 = ({data, filters, onClick}) => {
  //console.log(data, filters)
  const { offset, limit, count } = data;
  const currentPage = Math.ceil(offset / limit) + 1;
  const pageList = [];
  const qs = filtersToSearch(filters);
  for (let i=0; i<Math.ceil(count/limit);i++) {
    //return (<li key={i} className={(i==currentPage) ? 'active' : null}><a href="#" onClick={(e)=>props.onClick(e, offset=(i-1)*limit, limit=limit)}>{i}</a></li>);
    const p = i+1;
    const plusOrMinus = (offset > (i*limit)) ? 1 : -1;
    const pageOffset = i * limit;
    const pageUrl = `/occurrence/search/?${qs}&offset=${pageOffset}`;
    pageList.push(<li key={i} className={(p==currentPage) ? 'active' : null}><a href={pageUrl}>{p}</a></li>);
  }
  return (
      <div className="center-block text-center">
      <ul className="pagination">
        <li>
        <a href="#" aria-label="Previous">
            <span aria-hidden="true">&laquo;</span>
          </a>
        </li>
        {pageList}
        <li>
        <a href="#" aria-label="Next">
            <span aria-hidden="true">&raquo;</span>
          </a>
        </li>
      </ul>
    </div>
  );
};

export {fetchData, filtersToSearch, Pagination}
