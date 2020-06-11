import React, {useEffect, useState} from 'react';

import {Line, Bar} from 'react-chartjs-2';

import {fetchData} from './Utils';

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

  useEffect(() => {
    /*const fetchData = async (url) => {
      try {
        const resp = await fetch(url);
        let jsonData = await resp.json();
        console.log('init:', jsonData);
        yearChartData.labels = ['2008', '2009', '2010'];
        yearChartData.datasets[0].data =  [815, 975, 1919];
        setYearData(yearChartData);

      } catch(error) {
        // set err, error.toString()
      }
    };
    fetchData('/test_y');*/
    fetchData('/test_y').then((x) => {
      console.log(x);
      chartData.year.labels = ['2008', '2009', '2010'];
      chartData.year.datasets[0].data =  [815, 975, 1919];
      setYearData([true, chartData.year]);
    });
    fetchData('/test_m').then((x) => {
      console.log(x);
      const labels = [];
      const data = [];
      for( let i of x[1]) {
        labels.push(i.month);
        data.push(i.count);
      }
      setMonthData([true, chartData.month])
    });
  }, []);
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

      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
        <div className="tools-title">授權狀態</div>
          <div className="tools-content">
            <img src="https://fakeimg.pl/600x120/?text=chart" alt="" className="img-responsive" />
          </div>
        </div>
      </div>
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
      <tr>
      <td>Lycopodium veitchii Christ, GBIF Backbone Taxonomy</td>
      <td>67</td>
      <td>
      <div className="chart-bar-h-bg">
      <span className="chart-value-bg" style={{'width': '30%'}}></span>
      </div>
      </td>
      </tr>
      <tr>
      <td>Herbarium of Taiwan Forestry Research Institute</td>
      <td>64</td>
      <td>
      <div className="chart-bar-h-bg">
      <span className="chart-value-bg" style={{'width': '28%'}}></span>
      </div>
      </td>
      </tr>
      <tr>
      <td>The digitization of plant specimens of NTU</td>
      <td>21</td>
      <td>
      <div className="chart-bar-h-bg">
      <span className="chart-value-bg" style={{'width': '15%'}}></span>
      </div>
      </td>
      </tr>
      <tr>
      <td>Database of Native Plants in Taiwan</td>
      <td>19</td>
      <td>
      <div className="chart-bar-h-bg">
      <span className="chart-value-bg" style={{'width': '12%'}}></span>
      </div>
      </td>
      </tr>
      <tr>
      <td> The vascular plants collection (P) at the Herbarium</td>
      <td>12</td>
      <td>
      <div className="chart-bar-h-bg">
      <span className="chart-value-bg" style={{'width': '10%'}}></span>
      </div>
      </td>
      </tr>
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
