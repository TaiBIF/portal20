import React, {useEffect, useState, useRef} from 'react';
import { MapContainer, TileLayer, Marker, Popup, FeatureGroup, GeoJSON } from 'react-leaflet'
import { Icon } from 'leaflet';
import "./map.css";
import { EditControl } from "react-leaflet-draw"
import L from 'leaflet';

// export const icon = new Icon({
// iconUrl: '<i class="fa fa-circle"></i>',
// iconSize: [25, 25
// });
// import nationalParks from './national-parks.json';
// import treeMarker from './taibif-logo-rgb-s.jpg';
import {fetchData, filtersToSearch} from '../Utils';


const API_URL_PREFIX = `/api/v2/occurrence/map`;
const geojsonMarkerOptions = {
radius: 4,
fillColor: "#ff7800",
color: "transparent",
weight: 1,
opacity: 1,
fillOpacity: 0.8
};

            // L.geoJSON({
            //     "type": "Point",
            //     "coordinates": [
            //         -105.01621,
            //         39.57422
            //     ]
            // }, {
            //     pointToLayer: function (feature, latlng) {
            //         return L.circleMarker(latlng, geojsonMarkerOptions);
            //     }
            // }).addTo(map);

              
function OccurrenceMap(props) {

    function pointToLayer(feature, latlng) {
        return L.circleMarker(latlng, {
            radius: 4,
            fillColor: "#ff7800",
            color: "transparent",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
            }) // Change marker to circle
        }    
    
    const {filters} = props;
    const search = filtersToSearch(filters);
    const [jsonObject, setGeoJSON] = useState([false, []]);
    useEffect(() => {
        const apiURL = `${API_URL_PREFIX}?${search}`;
        console.log('fetch:', apiURL)
        fetchData(apiURL).then((data) => {
            setGeoJSON([true, data.map_geojson])
        });
    }, [filters]);
 
    function App(){
        
    return <div className="App">
    <MapContainer center={[23.5, 121.2]} zoom={7} >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; <a href=&quot;https://www.openstreetmap.org/copyright&quot;>OpenStreetMap</a> contributors" />
      <GeoJSON data={jsonObject} pointToLayer={pointToLayer}/>

        {/* circleMarker */}
      <FeatureGroup>
        <EditControl
        position="topright"
        draw={{
          marker: false,
          polygon: false,
          polyline: false,
          rectangle: true,
          circle: false,
          circlemarker: false
        }}
        edit={{edit: false}}
        />
        </FeatureGroup> 
    </MapContainer>
  </div>
    }

    //console.log(props);

    return (
        <React.Fragment>
        <div>
        <App />
        </div>
        </React.Fragment>
    );
  }


export {OccurrenceMap,}