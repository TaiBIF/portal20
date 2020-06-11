async function fetchData(url) {
  console.log('🙋', url);
  let response = await fetch(url);
  let data = await response.json();
  console.log( '🚍', data);
  return data;
}


export {fetchData}
