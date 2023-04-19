
function getColor(d) {
  return d > 1000 ? '#800026' :
         d > 500  ? '#BD0026' :
         d > 200  ? '#E31A1C' :
         d > 100  ? '#FC4E2A' :
         d > 50   ? '#FD8D3C' :
         d > 20   ? '#FEB24C' :
         d > 10   ? '#FED976' :
                    '#FFEDA0';
}

function getRadius(d) {
  return d > 1000 ? 11 :
         d > 500  ? 10 :
         d > 200  ? 9 :
         d > 100  ? 8 :
         d > 50   ? 7 :
         d > 20   ? 6 :
         d > 10   ? 5 :
                    4;
}  

function gerBorderColor(d) {
  return d > 20   ? 'transparent' :
                    '#FEB24C';
}  

const rank = document.currentScript.getAttribute('taxon_rank'); 
const id = document.currentScript.getAttribute('taxon_id'); 
const endpoint = `/api/v2/occurrence/search?path=${id}&facet=year&facet=month&facet=dataset&facet=dataset_id&facet=publisher&facet=country&facet=license`;

$.ajax({
  type: "GET",
  url: endpoint,
  dataType: "json",
  success: function (response) {
    L.geoJSON(response.map_geojson,{
      pointToLayer: function(feature, latlng) {
        return L.circleMarker(latlng, {
          radius: getRadius(feature.properties.counts),
          fillColor: getColor(feature.properties.counts),
          color: gerBorderColor(feature.properties.counts),
          weight: 1,
          opacity: 1,
          fillOpacity: 0.8
        }) // Change marker to circle
      } 
    }).addTo(map);
  },
  error: function (thrownError) {
    console.log(thrownError);
  }
});
const map = L.map('map').setView([0, 0], 2);

const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; <a href=&quot;https://www.openstreetmap.org/copyright&quot;>OpenStreetMap</a> contributors',
}).addTo(map);
