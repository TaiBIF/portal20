
const endpoint = 'https://data.taieol.tw/eol/endpoint/taxondesc/species/204491';
  $.ajax({
    type: "GET",
    url: endpoint,
    dataType: "json",
    success: function (response) {
      const charge = [];
      charge.push(...response);
      createDomElement(charge);
    },
    error: function (thrownError) {
      console.log(thrownError);
    }
  });

  function createDomElement(charge) {
    const domElements = charge.map( place => {
      return `
    <li>
      <p class="location">位置： ${ place.Location }</p>
      <p class="address">地址：${ place.Address }</p>
    </li>
  `;
    }).join("");

    const chargeList = document.querySelector('.charge-list');
    chargeList.innerHTML = domElements;
  }












