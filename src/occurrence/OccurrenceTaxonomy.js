import React, {useEffect, useState} from 'react';
7
//import {HorizontalBar} from 'react-chartjs-2';
import {fetchData, filtersToSearch} from '../Utils';

const taxonChartDataTmp = {
  labels: ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species'],
  datasets: [
    {
      label: 'Number of Taxonomy',
      backgroundColor: 'rgba(255,99,132,0.2)',
      borderColor: 'rgba(255,99,132,1)',
      borderWidth: 1,
      hoverBackgroundColor: 'rgba(255,99,132,0.4)',
      hoverBorderColor: 'rgba(255,99,132,1)',
      data: [], //[65, 59, 80, 81, 56, 55, 40]
    }
  ]
};


const API_URL_PREFIX = '/api/occurrence/taxonomy';
function OccurrenceTaxonomy(props) {
  const {filters} = props;
  const search = filtersToSearch(filters);

  const [taxonChartData, setTaxonChartData] = useState([false, []]);

  useEffect(() => {
    const apiURL = `${API_URL_PREFIX}/${search}`;
    fetchData(apiURL).then((data) => {
      let chartData = taxonChartDataTmp;
      chartData.datasets[0].data = data.search.taxon_num_list;
      setTaxonChartData([true, chartData])
    });
  }, []);

  return (
      <React.Fragment>
      <div className="col-xs-12">
        <div className="tools-intro-wrapper">
          <div className="tools-title">分類</div>
      <div className="tools-content">
      {/*
            { taxonChartData[0]
              ?  <HorizontalBar data={taxonChartData[1]} />
              : <img src="https://fakeimg.pl/600x120/?text=chart loading..." alt="" className="img-responsive" /> }
       */}
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
      </React.Fragment>
  )
}
export {OccurrenceTaxonomy, }


/*
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

*/
