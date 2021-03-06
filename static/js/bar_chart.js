
$(function() {
  $.ajax({
    url: 'http://127.0.0.1:8000/taxon_bar/',
    complete: function(json) {
      data = JSON.parse(json.responseText);
      // set some variable to host data
      var arrayString = [],


        array_final = []

      $.each(data[1], function(i, data) {
        // fill the date array

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
          type: 'bar',
          renderTo: 'container'
        },
        title: {
          text: 'Occurrence data'
        },
        plotOptions: {
          bar: {
            dataLabels: {
                enabled: true
            }
          }
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            x: -40,
            y: 80,
            floating: true,
            borderWidth: 1,
            backgroundColor:
                Highcharts.defaultOptions.legend.backgroundColor || '#FFFFFF',
            shadow: true
        },
        xAxis: {
          categories: ['Kingdom', 'Phylum', 'Class', 'Order', 'Family','Genus','Species'],

        },
        yAxis: {
            min: 0,
            title: {
                text: 'Occurrence',
                align: 'high'
            },
            labels: {
                overflow: 'justify'
            }
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
