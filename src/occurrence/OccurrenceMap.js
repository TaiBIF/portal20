import React, {useEffect, useState, useRef} from 'react';
import { Route, Link, Switch } from "react-router-dom"
import ReactDOMServer from "react-dom/server";

import { MapContainer, TileLayer, Marker, Popup, FeatureGroup, GeoJSON } from 'react-leaflet'
import { featureGroup, Icon } from 'leaflet';
import "./map.css";
import { EditControl } from "react-leaflet-draw"
import L from 'leaflet';
import {fetchData, filtersToSearch} from '../Utils';

const API_URL_PREFIX = `/api/v2/occurrence/map`;

export default function OccurrenceMap(props) {

    /* marker style */
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

    function pointToLayer(feature, latlng) {
        return L.circleMarker(latlng, {
            radius: getRadius(feature.properties.counts),
            fillColor: getColor(feature.properties.counts),
            color: gerBorderColor(feature.properties.counts),
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
            }) // Change marker to circle
        }    
    /* marker style */
    const {filters} = props;
    const search = filtersToSearch(filters);
    const [jsonObject, setGeoJSON] = useState([false, []]);
    const [isLoaded, setLoading] = useState(false);
    useEffect(() => {
        const apiURL = `${API_URL_PREFIX}?${search}`;
        console.log('fetch:', apiURL)
        fetchData(apiURL).then((data) => {
            setGeoJSON([true, data.map_geojson])
            setLoading(true)
        });
    }, [filters]);


    // const GetSpecies = () => {
    //     // console.log('hi')
    //     // const [speciesData, setSpeciesData] = useState([false, []]);
    //     // // useEffect(() => {
    //     //     //const apiURL = `/api/v2/occurrence/get_map_species`;
    //     // console.log('fetch:')
        
    //     fetchData('http://127.0.0.1:8000/api/v2/occurrence/get_map_species?pk=8').then((data) => {
    //         setSpeciesData([true, data.test])
    //         // return <a id="search-by-map">以此經緯度範圍搜尋出現紀錄➡️{data.test}</a>
    //     });

    //         };
    function App(){
        const onCreated = e => {

            // get current lat & lon
            let bounds = e.layer.getLatLngs();
            // round coordinates to 5 digits    
            let lat = [];
            let lng = [];
            for (let step = 0; step < 4; step++) {
                if (!lat.includes(Math.round(bounds[0][step]['lat'] * 100000) / 100000)){
                    lat.push(Math.round(bounds[0][step]['lat'] * 100000) / 100000)
                }
                if (!lng.includes(Math.round(bounds[0][step]['lng'] * 100000) / 100000)){
                    lng.push(Math.round(bounds[0][step]['lng'] * 100000) / 100000)
                }
            }
            let latStr = encodeURIComponent(lat);
            let lngStr = encodeURIComponent(lng);

            // get occurrence data ordered by species
            $.ajax({
                url: `http://127.0.0.1:8000/api/v2/occurrence/get_map_species?lat=${latStr}&lng=${lngStr}`,
            // set other AJAX options
            }).done((response) => {
                console.log('resppp', response, url)


                const OccurrenceSpeciesData = () => {
                    return <div>
                    
                    <a id="search-by-map">以此經緯度範圍搜尋出現紀錄➡️{response.taxon}</a>
                    </div>
                }


            // remove previous layer
            const drawnItems = featureGroupRef.current._layers;
            if (Object.keys(drawnItems).length > 1) {
                Object.keys(drawnItems).forEach((layerid, index) => {
                    if (index > 0) return;
                    const layer = drawnItems[layerid];
                    featureGroupRef.current.removeLayer(layer);
                });
            }
            // popup
            e.layer.bindPopup(ReactDOMServer.renderToString(<OccurrenceSpeciesData/>),{closeButton: false}).openPopup();
            document.querySelector(`#search-by-map`).addEventListener('click', function(){
                //redirect to OccurrenceSearch
                let current_path = window.location.href
                current_path = current_path.split('?')[0]
                let new_path = current_path.replace('map','search')
                if (search!==''){
                    new_path = new_path = new_path + '?' + search + '&lat=' + latStr + '&lng=' + lngStr}
                else {
                    new_path = new_path = new_path + '?lat=' + latStr + '&lng=' + lngStr
                }
                window.location = new_path
            })

            })
        };
            
            const featureGroupRef = useRef()

            return <div className="App">
            <MapContainer center={[0, 0]} zoom={2} >
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; <a href=&quot;https://www.openstreetmap.org/copyright&quot;>OpenStreetMap</a> contributors" />
            <GeoJSON data={jsonObject} pointToLayer={pointToLayer}/>
            <FeatureGroup ref={featureGroupRef}>
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
                onCreated={onCreated}
                />
                </FeatureGroup> 
            </MapContainer>
        </div>
    }
    return (  
        <React.Fragment>
        {!isLoaded ? <div className="search-loading"> 🌱 Loading... ⏳ </div> : <div><App /></div>}    
        </React.Fragment>
    );
  }


// export {OccurrenceMap,}