import React, {useEffect, useState} from 'react';
import {Line, Bar} from 'react-chartjs-2';
import {fetchData, filtersToSearch} from '../Utils';
import ReactTooltip from 'react-tooltip';
import { Pagination } from '../Utils';

const chartData = {
  year: {
    labels: [],
    datasets: [
      {
        label: '每年出現紀錄',
        fill: false,
        lineTension: 0.1,
        backgroundColor: '#7DC49D',
        borderColor: '#74B175',
        borderCapStyle: 'butt',
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: 'miter',
        pointBorderColor: '#7DC49D',
        pointBackgroundColor: '#74B175',
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#7DC49D',
        pointHoverBorderColor: '#74B175',
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
        backgroundColor: '#74B175',
        borderColor: '#7DC49D',
        borderWidth: 1,
        hoverBackgroundColor: '#7DC49D',
        hoverBorderColor: '#74B175',
        barPercentage: 1.0,
        categoryPercentage: 1.0,
        data: []
      }
    ]
  }
};

const chartData_e = {
  year: {
    labels: [],
    datasets: [
      {
        label: 'Occurrence record per year',
        fill: false,
        lineTension: 0.1,
        backgroundColor: '#7DC49D',
        borderColor: '#74B175',
        borderCapStyle: 'butt',
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: 'miter',
        pointBorderColor: '#7DC49D',
        pointBackgroundColor: '#74B175',
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#7DC49D',
        pointHoverBorderColor: '#74B175',
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
        label: 'Occurrence record per month',
        backgroundColor: '#74B175',
        borderColor: '#7DC49D',
        borderWidth: 1,
        hoverBackgroundColor: '#7DC49D',
        hoverBorderColor: '#74B175',
        barPercentage: 1.0,
        categoryPercentage: 1.0,
        data: []
      }
    ]
  }
};

const API_URL_PREFIX = `/api/v1/occurrence/charts`;
const facetQueryString = `facet=year&facet=month&facet=dataset&facet=dataset_id&facet=publisher&facet=country&facet=license`;
      

const sortData = (objs) => {
  return Object.keys(objs).sort().reduce(
    (obj, key) => { 
      obj[key] = objs[key]; 
      return obj;
    }, 
    {}
  );
}

function OccurrenceCharts(props) {
  const {filters} = props;
  const search = filtersToSearch(filters);

  const [yearData, setYearData] = useState([false, {}]);
  const [monthData, setMonthData] = useState([false, {}]);
  const [datasetData, setDatasetData] = useState([false, []]);
  const [offset, setOffset] = useState(0);
  const limit = 10;
  
  useEffect(() => {
    let apiURL = null;
    if(search){
      apiURL = `${API_URL_PREFIX}?${search}&${facetQueryString}`;
    }else{
      apiURL = `${API_URL_PREFIX}?${facetQueryString}`;
    }
    if (props.language === 'zh-hant'){
    fetchData(apiURL).then((data) => {
      
      const year = chartData.year;
      let dataCount = {}
      let ordered = []
      data.charts[0].rows.forEach(row => {
        dataCount = {...dataCount,[row.label]:row.count}
      });

      ordered = sortData(dataCount)
    
      year.labels = Object.keys(ordered)
      year.datasets[0].data =  Object.values(ordered);
      setYearData([true, year]);

      const month = chartData.month;
      dataCount = {}
      data.charts[1].rows.forEach(row => {
        dataCount = {...dataCount,[row.label]:row.count}
      });
      ordered = sortData(dataCount)
    
      month.labels = Object.keys(ordered)
      month.datasets[0].data =  Object.values(ordered);

      setMonthData([true, month])

      let num_occurrence_max = 0;
      const newData = data.charts[2].rows.map((row, i) => {
        if (i === 0) {
          num_occurrence_max = row.count;
        }
        const p = Math.round(row.count / num_occurrence_max * 100);

        return {key:row.key,title:row.label,num_occurrence:row.count,percent:p};
      });
      setDatasetData([true, newData])
    });}
    else{fetchData(apiURL).then((data) => {
      
      const year = chartData_e.year;
      let dataCount = {}
      let ordered = []
      data.charts[0].rows.forEach(row => {
        dataCount = {...dataCount,[row.label]:row.count}
      });

      ordered = sortData(dataCount)
    
      year.labels = Object.keys(ordered)
      year.datasets[0].data =  Object.values(ordered);
      setYearData([true, year]);

      const month = chartData_e.month;
      dataCount = {}
      data.charts[1].rows.forEach(row => {
        dataCount = {...dataCount,[row.label]:row.count}
      });
      ordered = sortData(dataCount)
    
      month.labels = Object.keys(ordered)
      month.datasets[0].data =  Object.values(ordered);

      setMonthData([true, month])

      let num_occurrence_max = 0;
      const newData = data.charts[2].rows.map((row, i) => {
        if (i === 0) {
          num_occurrence_max = row.count;
        }
        const p = Math.round(row.count / num_occurrence_max * 100);

        return {key:row.key,title:row.label,num_occurrence:row.count,percent:p};
      });
      setDatasetData([true, newData])
    });}

    
  }, [filters]);

  function DatasetDataBody() {
    return datasetData[1].map((x,index) => {
      // const q = encodeURIComponent(x.label);
      return (
        index >= offset && index <= offset+limit ?
        <tr key={x.title}>
          <td>
            <a href={`/occurrence/search?dataset=${x.key}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-link" viewBox="0 0 16 16">
                <path d="M6.354 5.5H4a3 3 0 0 0 0 6h3a3 3 0 0 0 2.83-4H9c-.086 0-.17.01-.25.031A2 2 0 0 1 7 10.5H4a2 2 0 1 1 0-4h1.535c.218-.376.495-.714.82-1z"/>
                <path d="M9 5.5a3 3 0 0 0-2.83 4h1.098A2 2 0 0 1 9 6.5h3a2 2 0 1 1 0 4h-1.535a4.02 4.02 0 0 1-.82 1H12a3 3 0 1 0 0-6H9z"/>
              </svg>
            </a>
          </td>
          <td>{x.title}</td>
          <td>{x.num_occurrence}</td>
          <td>
          <div className="chart-bar-h-bg">
          <span className="chart-value-bg" style={{'width': x.percent+'%'}}></span>
          </div>
          </td>
        </tr>
        : "");
    });
  }

  const handlePaginationOnClick = (pageOffset) => {
    console.log('pageOffset',pageOffset)
    setOffset(pageOffset)
    console.log('pageOffset',pageOffset)
  }

  return (
      <React.Fragment>
      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
          { props.language === 'en'? 
            <div className="tools-title" data-tip='Occurrence record per month: Display only record with month provided, value is the number of cumulative records'><span className="glyphicon glyphicon-info-sign"></span>Month</div>
            :
            <div className="tools-title" data-tip='每月出現紀錄：僅顯示有提供月份之出現紀錄筆數，為歷年月份資料筆數累計值'><span className="glyphicon glyphicon-info-sign"></span>月份</div>
          }
            <div className="tools-content">
            { monthData[0]
              ? <Bar
                 height={400}
                 data={monthData[1]}
                 options={{
                    maintainAspectRatio: false,
                    legend: {
                      display: true,
                      position: "bottom"
                    },
                    scales: {
                      x: {
                          grid: {
                            display: false
                          }
                      },
                      y: {
                        grid: {
                          display: false
                        }
                      }
                    }
                 }}
              />
              : <img src="https://fakeimg.pl/600x120/?text=chart loading..." alt="" className="img-responsive" /> }
          </div>
        </div>
      </div>

      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
        { props.language === 'en'? 
            <div className="tools-title" data-tip='Occurrence record per year: Display only record with year provided'><span className="glyphicon glyphicon-info-sign"></span>Year</div>
            :
            <div className="tools-title" data-tip='每年出現紀錄：僅顯示有提供年份之出現紀錄筆數'><span className="glyphicon glyphicon-info-sign"></span>年份</div>
          }
      
          <div className="tools-content">
          { yearData[0]
            ? <Line data={yearData[1]} options={{
              legend: {
                display: true,
                position: "bottom"
              },
              title: {
                position: 'bottom',
                align: 'center',
              },
              scales: {
                x: {
                    grid: {
                      display: false
                    }
                },
                y: {
                  grid: {
                    display: false
                  }
                }
              }}}/>
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
      { props.language === 'en'?
      <div className="tools-title">Dataset</div>
      :
      <div className="tools-title">資料集</div>
      }
      
      <div className="tools-content">
      <div className="table-responsive">
      <table className="table borderless" id="occurence-charts-dataset-table">
      <thead>
      { props.language === 'en'?
      <tr>
      <th>&nbsp;</th>
      <th className=" bg-transparent">Dataset Name</th>
      <th>Numbers</th>
      <th>&nbsp;</th>
      </tr>
      :
      <tr>
      <th>&nbsp;</th>
      <th className=" bg-transparent">資料集</th>
      <th>出現次數</th>
      <th>&nbsp;</th>
      </tr>
      }
      
      </thead>
      <tbody>
      {datasetData[0] ? <DatasetDataBody />: null}
      </tbody>
      </table>
      {datasetData[1].length ? <Pagination total={datasetData[1].length} offset={offset} urlPrefix='#occurence-charts-dataset-table' limit={limit} handleOnClick={handlePaginationOnClick}/> : ''}
      </div>
      </div>
      </div>
      </div>
      <ReactTooltip />
      </React.Fragment>
  )
}
export {OccurrenceCharts, }

