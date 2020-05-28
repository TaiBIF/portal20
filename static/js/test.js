$(function() {


  $.ajax({
    url: 'http://127.0.0.1:8000/test2',
    complete: function(json) {
      data = JSON.parse(json.responseText);
      // set some variable to host data
      var arrayString = [],
        year_list = [],
        array_final = []

      $.each(data[1], function(i, data) {
        //Store indicator name
        country_name = data.key;
        // Store indicator label
        indicatorName = data.label;
        // fill the date array
        year_list.push(data.year);
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
          renderTo: 'container'
        },
        title: {
          text: indicatorName
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
        subtitle: {
          text: 'Source: World Bank Data'
        },
        xAxis: {
          categories: year_list.reverse() //.reverse() to have the min year on the left
        },
        series: [{
          name: country_name,
          data: array_final.reverse() //
        }]
      });

    },
    error: function() {
      console.log('there was an error!');
    }
  });

});
