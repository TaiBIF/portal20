
$(function() {
  $.ajax({
    url: 'http://127.0.0.1:8000/test3',
    complete: function(json) {
      data = JSON.parse(json.responseText);
      // set some variable to host data
      var arrayString = [],
        year_list = [],
        array_final = []

      $.each(data[1], function(i, data) {

        // fill the date array
        year_list.push(data.month);
        // fill the string data array
        arrayString.push(data.count);
      });

      // querry send string that we need to convert into numbers
      for (var i = 0; i < arrayString.length; i++) {
        if (arrayString[i] != null) {
          array_final.push(parseFloat(arrayString[i]))
        } else {
          array_final.push(null)
        };
      }

      var chart = new Highcharts.Chart({
        chart: {
          type: 'spline',
          renderTo: 'container2'
        },
        title: {
          text: 'Occurrence data'
        },
        tooltip: {
          valueDecimals: 2,
          pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>{point.y}%</b><br/>'
        },
        plotOptions: {
          series: {
            marker: {
              enabled: false
            }
          }
        },

        xAxis: {
          categories: year_list.reverse() //.reverse() to have the min year on the left
        },
        series: [{
          data: array_final.reverse() //
        }]
      });

    },
    error: function() {
      console.log('there was an error!');
    }
  });

});
