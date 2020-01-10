import React from 'react';

function SearchMainOccurrence(props) {
  return <h1>Ourr</h1>
}

function SearchMainDataset(props) {
  //console.log(props);
  const rows = props.data.results.map((row) => {
    return (
        <div className="row listbox-img-right-wrapper" key={row.id}>
        <div className="col-xs-8">
        <span className="label label-warning">{row.dwc_core_type}</span>
        <h3 className="listbox-inner-title">{ row.title }</h3>
        <p className="listbox-inner-summary hidden-xs">
        {row.description}
        </p>
        <span className="badge">紀錄數量: {row.num_record} </span>
        <div><a href={"/dataset/"+row.name} className="">觀看資料集</a></div>
        </div>
        </div>
    )
  });

  return (
      <div className="col-xs-12 col-md-9">
      <div className="container">
      <h1 className="heading-lg-ul">資料集
      <span className="heading-footnote"> 共 {props.data.count} 筆資料</span>
      </h1>
      {rows}
      </div>
      </div>
  )
}

function SearchMain(props) {
  if (props.searchType === 'dataset') {
    return <SearchMainDataset data={props.data} searchType={props.searchType} />
  }
  else if (props.searchType === 'occurrence') {
    return <SearchMainOccurrence data={props.data} searchType={props.searchType} />
  }
}

export default SearchMain;
