import React, {useEffect, useState} from 'react';

import OccurrenceSearch from './OccurrenceSearch';
import {OccurrenceCharts} from './OccurrenceCharts';
import {OccurrenceTaxonomy} from './OccurrenceTaxonomy';
import {OccurrenceDownload} from './OccurrenceDownload';
import OccurrenceMap from './OccurrenceMap';
import {Pagination} from '../Utils'

import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
  useLocation
} from "react-router-dom";

const navTabsData = [
  {
    'key': 'Search',
    'label': '資料列表',
    'path': '/occurrence/search/',
  },
  {
    'key': 'gallery',
    'label': '影像集',
    'path': '/occurrence/gallery/',
    'disable': true,
  },
  {
    'key': 'Map',
    'label': '分佈地圖',
    'path': '/occurrence/map/',
    //'disable': true,
  },
  {
    'key': 'taxonomy',
    'label': '分類系統',
    'path': '/occurrence/taxonomy/',
    'disable': true,
  },
  {
    'key': 'charts',
    'label': '指標',
    'path': '/occurrence/charts/',
  },
  {
    'key': 'Download',
    'label': '下載',
    'path': '/occurrence/download/',
  }
];

const OccurrenceRouter = ({data, filters,urlPrefix, language}) =>  {
  //console.log(data);
  const path = window.location.pathname;
  const m = path.match(/\/occurrence\/(search|map|gallery|taxonomy|charts|download)/);
  const initTab = (m[1]) ? m[1] : 'search';

  const [activeTab, setActiveTab] = useState(initTab);
  const navTabs = [];
  for (let i in navTabsData) {
    const key = navTabsData[i].key;
    if (!navTabsData[i].disable) {
      navTabs.push(
          <li key={key} className={activeTab === key ? "active" : null} onClick={(e)=>setActiveTab(key)}>
          <Link to={navTabsData[i].path}>{language === 'en' ? navTabsData[i].key : navTabsData[i].label}</Link>
          </li>
      );
    }
  }
  /*{navTabsData.map((x) => (
      <li key={x.key} className={activeTab === x.key ? "active" : null} onClick={(e)=>setActiveTab(x.key)}>
      <Link to={x.path}>{x.label}</Link>
      </li>))}*/
  return (
      <Router>
      <div className="table-responsive">
      <ul className="nav nav-tabs nav-justified search-content-tab">
      {navTabs.map((x) => x)}
      </ul>
      </div>
      <Switch>
        <Route path={navTabsData[0].path}>
          <OccurrenceSearch data={data} language={language} />
          <Pagination offset={data.offset} total={data.count} urlPrefix={urlPrefix} />
        </Route>
        <Route path={navTabsData[2].path}>
          <OccurrenceMap data={data} filters={filters} language={language} />
        </Route>
        <Route path={navTabsData[4].path}>
      <OccurrenceCharts filters={filters} language={language} />
        </Route>
        <Route path={navTabsData[3].path}>
      <OccurrenceTaxonomy filters={filters} language={language} />
        </Route>
        <Route path={navTabsData[5].path}>
      <OccurrenceDownload filters={filters} data={data} language={language} />
        </Route>
      </Switch>
      </Router>
  );
}

export default OccurrenceRouter;
