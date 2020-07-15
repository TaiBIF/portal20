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

export {fetchData, filtersToSearch}
