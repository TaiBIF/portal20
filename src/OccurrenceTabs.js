import React, {useEffect} from 'react';

function OccurrenceCharts(props) {
  //const qs = (queryList.length > 0) ? '?' + queryList.join('&') : '';
  useEffect(() => {
    const fetchData = async () => {
      try {
        const resp = await fetch('/api/occurrence/charts');
        let jsonData = await resp.json();
        console.log('init:', jsonData);
        //setMenu(jsonData.menu);
        //setData(jsonData.search);
        //setDataLimit(jsonData.search.limit)
      } catch(error) {
        // set err, error.toString()
      }
    };
    fetchData();
  }, []);
  return (
    <React.Fragment>
                <div className="col-xs-12">
                  <div className="tools-intro-wrapper">
                    <div className="tools-title">月份</div>
                    <div className="tools-content">
                      <img src="https://fakeimg.pl/600x120/?text=chart" alt="" className="img-responsive" />
                    </div>
                  </div>
                </div>

                <div className="col-xs-12">
                  <div className="tools-intro-wrapper">
                    <div className="tools-title">年份</div>
                    <div className="tools-content">
                      <img src="https://fakeimg.pl/600x120/?text=chart" alt="" className="img-responsive" />
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
