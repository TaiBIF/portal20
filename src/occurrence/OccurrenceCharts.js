import React, {useEffect, useState} from 'react';
7
import {Line, Bar} from 'react-chartjs-2';

import {fetchData} from '../Utils';

const chartData = {
  year: {
    labels: [],
    datasets: [
      {
        label: '每年出現紀錄',
        fill: false,
        lineTension: 0.1,
        backgroundColor: 'rgba(75,192,192,0.4)',
        borderColor: 'rgba(75,192,192,1)',
        borderCapStyle: 'butt',
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: 'miter',
        pointBorderColor: 'rgba(75,192,192,1)',
        pointBackgroundColor: '#fff',
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: 'rgba(75,192,192,1)',
        pointHoverBorderColor: 'rgba(220,220,220,1)',
        pointHoverBorderWidth: 2,
        pointRadius: 1,
        pointHitRadius: 10,
        data: [],
      }
    ]
  },
  month: {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    datasets: [
      {
        label: '每月出現紀錄',
        backgroundColor: 'rgba(255,99,132,0.2)',
        borderColor: 'rgba(255,99,132,1)',
        borderWidth: 1,
        hoverBackgroundColor: 'rgba(255,99,132,0.4)',
        hoverBorderColor: 'rgba(255,99,132,1)',
        data: []
      }
    ]
  }
};

function OccurrenceCharts(props) {
  //const qs = (queryList.length > 0) ? '?' + queryList.join('&') : '';
  const [yearData, setYearData] = useState([false, {}]);
  const [monthData, setMonthData] = useState([false, {}]);
  const [datasetData, setDatasetData] = useState([false, []]);

  useEffect(() => {
    fetchData('/api/occurrence/charts/?chart=year').then((data) => {
      const year = chartData.year;
      year.labels = data.search[0];
      year.datasets[0].data =  data.search[1];
      setYearData([true, year]);
    });
  }, []);
  useEffect(() => {
    fetchData('/api/occurrence/charts/?chart=month').then((data) => {
      const month = chartData.month;
      month.labels = data.search[0];
      month.datasets[0].data =  data.search[1];
      setMonthData([true, month])
    });
  }, []);
  useEffect(() => {
    fetchData('/api/occurrence/charts/?chart=dataset').then((data) => {
      let num_occurrence_max = 0;
      const newData = data.search.map((x, i) => {
        if (i === 0) {
          num_occurrence_max = x['num_occurrence'];
        } 
        const p = Math.round(x['num_occurrence'] / num_occurrence_max * 100);
        x['num_occurrence'] = x['num_occurrence'].toLocaleString('en');
        x['percent'] = p;
        return x;
      });
      setDatasetData([true, data.search])
    });
  }, []);

  function DatasetDataBody() {
    return datasetData[1].map((x) => {
      return (
        <tr key={x.title}>
        <td>{x.title}</td>
        <td>{x.num_occurrence}</td>
        <td>
        <div className="chart-bar-h-bg">
        <span className="chart-value-bg" style={{'width': x.percent+'%'}}></span>
        </div>
        </td>
        </tr>);
    });
  }
  return (
      <React.Fragment>
      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
          <div className="tools-title">月份</div>
            <div className="tools-content">
            { monthData[0]
              ? <Bar
                 data={monthData[1]}
                 options={{
                   maintainAspectRatio: false
                 }}
              />
              : <img src="https://fakeimg.pl/600x120/?text=chart loading..." alt="" className="img-responsive" /> }
          </div>
        </div>
      </div>

      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
      <div className="tools-title">年份</div>
          <div className="tools-content">
          { yearData[0]
            ? <Line data={yearData[1]} />
            : <img src="https://fakeimg.pl/600x120/?text=chart loading..." alt="" className="img-responsive" /> }
         </div>
        </div>
      </div>

    {/*
      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
        <div className="tools-title">授權狀態</div>
          <div className="tools-content">
            <img src="https://fakeimg.pl/600x120/?text=chart" alt="" className="img-responsive" />
          </div>
        </div>
      </div>
     */}
      <div className="col-xs-12">
      <div className="tools-intro-wrapper">
      <div className="tools-title">資料集</div>
      <div className="tools-content">
      <div className="table-responsive">
      <table className="table table-bordered">
      <thead>
      <tr>
      <th>資料集</th>
      <th>出現次數</th>
      <th>&nbsp;</th>
      </tr>
      </thead>
      <tbody>
      {datasetData[0] ? <DatasetDataBody />: null}
      </tbody>
      </table>
      </div>
      </div>
      </div>
      </div>
      </React.Fragment>
  )
}
export {OccurrenceCharts, }
