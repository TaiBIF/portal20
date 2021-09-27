async function fetchData(url) {
  if(/^year=/.test(url))
    url = url.replace("-",",")
    
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
    
    if(/^year=/.test(item))
      item = item.replace("-",",")

    console.log('item',item)
    qsArr.push(item);
  });
  return qsArr.join('&');
}

export {fetchData, filtersToSearch}
