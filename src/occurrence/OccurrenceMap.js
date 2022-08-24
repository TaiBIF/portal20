import React, {useEffect, useState, useRef} from 'react';
import { Route, Link, Switch } from "react-router-dom"
import ReactDOMServer from "react-dom/server";
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, FeatureGroup, GeoJSON } from 'react-leaflet'
import { featureGroup, Icon } from 'leaflet';
import "./map.css";
import { EditControl } from "react-leaflet-draw"
import "./CustomMapTooltip"
import {fetchData, filtersToSearch} from '../Utils';

const API_URL_PREFIX = `/api/v2/occurrence/map`;

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

    function popMsg(props,response,rows){
        let popMsg = null;
        if (props.language === 'en') {
            popMsg = (
                <div className="pop-msg">
                    <h4>Occurrence record within this range</h4>
                    <ul style={{listStyleType: "none", padding:0}}>{rows}</ul>
                    <p>{response.count} Result</p>
                    <a id="search-by-map">Use latitude and longitude range as filter ➡️</a>
                    </div>)
        }else{
            popMsg=(
                <div className="pop-msg">
                <h4>在此範圍內的出現紀錄</h4>
                <ul style={{listStyleType: "none", padding:0}}>{rows}</ul>
                <p>共 {response.count} 筆</p>
                <a id="search-by-map">以此經緯度範圍作為篩選條件➡️</a>
                </div>)
            }

        return popMsg
    }

export default function OccurrenceMap(props) {
   
    const {filters} = props;
    const search = filtersToSearch(filters);
    // const [jsonObject, setGeoJSON] = useState([false, []]);
    // const [isLoaded, setLoading] = useState(false);
    // useEffect(() => {
    //     const apiURL = `${API_URL_PREFIX}?${search}`;
    //     console.log('fetch:', apiURL)
    //     fetchData(apiURL).then((data) => {
    //         setGeoJSON([true, data.map_geojson])
    //         setLoading(true)
    //     });
    // }, [filters]);

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

            let current_path = window.location.href
            current_path = current_path.split('?')[0]

            let api_url;
            if (search!==''){
                api_url = `/api/v2/occurrence/get_map_species?${search}&lat=${lat[0]}&lat=${lat[1]}&lng=${lng[0]}&lng=${lng[1]}`
            }else {
                api_url = `/api/v2/occurrence/get_map_species?lat=${lat[0]}&lat=${lat[1]}&lng=${lng[0]}&lng=${lng[1]}`
            }

            

            $.ajax({
                url: api_url,
            // set other AJAX options
            }).done((response) => {

                const OccurrenceSpeciesData = () => {
                    const rows = response.results.map((row, index) => {
                        return (
                            <li key={index}><a href={"/occurrence/"+row.taibif_occ_id}>{row.scientificName} {row.name_zh}</a></li>
                        )
                    })
                    // http://jsfiddle.net/gq5Wf/6/
                    return popMsg(props,response,rows)
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
                    new_path = new_path = new_path + '?' + search + `&lat=${lat[0]}&lat=${lat[1]}&lng=${lng[0]}&lng=${lng[1]}`}
                else {
                    new_path = new_path = new_path + `?lat=${lat[0]}&lat=${lat[1]}&lng=${lng[0]}&lng=${lng[1]}`
                }

                //console.log(new_path)
                window.location = new_path
                
            })

            })
        };
            
            const featureGroupRef = useRef()

            return <div className="App">
            <MapContainer center={[0, 0]} zoom={2}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; <a href=&quot;https://www.openstreetmap.org/copyright&quot;>OpenStreetMap</a> contributors" />
            <GeoJSON data={props.data.map_geojson} pointToLayer={pointToLayer}/>
            <FeatureGroup ref={featureGroupRef}>
                <EditControl
                position="topright"
                draw={{
                marker: false,
                polygon: false,
                polyline: false,
                rectangle: {"showArea": false},
                circle: false,
                circlemarker: false
                }}
                edit={{edit: false}}
                onCreated={onCreated}
                />
                {/* {(L.drawLocal.draw.handlers.rectangle.tooltip.start = "hola")} */}
                </FeatureGroup> 
            </MapContainer>
        </div>
    }

    
    return (  
        <React.Fragment>
            {<App />}    
        {/* {!isLoaded ? <div className="search-loading"> 🌱 Loading... ⏳ </div> : <div><App /></div>}     */}
        </React.Fragment>
    );
  }


// export {OccurrenceMap,}
