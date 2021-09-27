import React from 'react';

async function fetchData(url) {
  console.log('🙋', url);
  let response = await fetch(url);
  let data = await response.json();
  console.log( '🚍', data);
  return data;
}

function filtersToSearch (filters) {
  //TODO: Array.from(filters).join('&');
  const qsArr = [];
  filters.forEach((item)=> {
    qsArr.push(item);
  });
  return qsArr.join('&');
}

const Pagination = ({data, filters, onClick}) => {
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
