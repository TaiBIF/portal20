import React, {useEffect, useState} from 'react';

import OccurrenceSearch from './occurrence/OccurrenceSearch';
import {OccurrenceCharts} from './occurrence/OccurrenceCharts';

import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
  useLocation
} from "react-router-dom";

const navTabsData = [
  {
    'key': 'search',
    'label': '資料列表',
    'path': '/occurrence/search/',
  },
  {
    'key': 'gallery',
    'label': '影像集',
    'path': '/occurrence/gallery/',
  },
  {
    'key': 'map',
    'label': '分佈地圖',
    'path': '/occurrence/map/',
  },
  {
    'key': 'taxonomy',
    'label': '分類系統',
    'path': '/occurrence/taxonomy/',
  },
  {
    'key': 'charts',
    'label': '指標',
    'path': '/occurrence/charts/',
  },
  {
    'key': 'download',
    'label': '下載',
    'path': '/occurrence/download/',
  }
];

const OccurrenceRouter = ({data}) =>  {
  console.log(data);
  const path = window.location.pathname;
  const m = path.match(/\/occurrence\/(search|map|gallery|taxonomy|charts|download)/);
  const initTab = (m[1]) ? m[1] : 'search';
  const [activeTab, setActiveTab] = useState(initTab);
  return (
      <Router>
      <div className="table-responsive">
      <ul className="nav nav-tabs nav-justified search-content-tab">
        {navTabsData.map((x) => (
            <li key={x.key} className={activeTab === x.key ? "active" : null} onClick={(e)=>setActiveTab(x.key)}>
            <Link to={x.path}>{x.label}</Link>
          </li>))}
      </ul>
      </div>
      <Switch>
        <Route path={navTabsData[0].path}>
          <OccurrenceSearch data={data} />
        </Route>
        <Route path={navTabsData[4].path}>
          <OccurrenceCharts />
        </Route>
      </Switch>
      </Router>
  );
}

export default OccurrenceRouter;
