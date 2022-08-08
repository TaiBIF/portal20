
var width = 980;
var height = 380;
var padding = 80;


const colorPrimary = '#846C5B';
const colorSecondary = '#BB998B';
const language = document.getElementById('dataset-table-container').lang;
// console.log("language ==== ", language)

function renderBarChart(selector, dataset) {

  var svg = d3.select(selector).append("svg").attr("width", 1200).attr("height", height);

  var xScale = d3.scaleBand()
    .rangeRound([padding, width - padding])
    .padding(0.5)
    .domain(dataset.map(function(d) { return d.x; }));

  var yScale = d3.scaleLinear()
    .domain([0, d3.max(dataset, function(d) { return d.y; })|| 1])
    .range([height - padding, padding]);

  svg.append("g")
    .attr("transform", "translate(" + 0 + "," + (height - padding) + ")")
    .attr("class", "axis")
    .call(d3.axisBottom(xScale));
  if (selector == '#taibif-stats__this_year_occurrence') {
  svg.append("g")
    .attr("transform", "translate(" + padding + "," + 0 + ")")
    .attr("class", "axis")
    .call(d3.axisLeft(yScale).ticks(5)
    .tickFormat(function (d) {
                switch(d) {
                  case 1000000: return "1M"; break;
                  case 2000000: return "2M"; break;
                  case 3000000: return "3M"; break;
                  case 4000000: return "4M"; break;
                  case 5000000: return "5M"; break;
              }})
      );
  } else {
    svg.append("g")
      .attr("transform", "translate(" + padding + "," + 0 + ")")
      .attr("class", "axis")
      .call(d3.axisLeft(yScale).ticks(5));
  };

  svg.append("g")
    .selectAll("rect")
    .data(dataset)
    .enter()
    .append("rect")
    .attr("x", function(d) { return xScale(d.x); })
    .attr("y", function(d) { return yScale(d.y); })
    .attr("width", xScale.bandwidth())
    .attr("height", function(d) { return height - padding - yScale(d.y); })
    .attr("fill", "#846C5B");

  svg.append("g")
    .selectAll("rect")
    .data(dataset)
    .enter()
    .append("text")
    .attr("x", function(d) { return xScale(d.x)+14; })
    .attr("y", function(d) {return yScale(d.y)-5; })
    .text(function(d) {return d.y.toLocaleString()})
    .attr("class", "label");
    const titleColor = colorPrimary;
    const appendixColor = colorPrimary;//'#1d5a91';
    const appendixColor2 = colorSecondary;//'#1d5a91';
    const yUnitTitle = (selector == '#taibif-stats__this_year_occurrence') ? '筆  數' : '個  數';
    // add graph title
  svg.append("text")
      .attr("x", 500)
      .attr("y", height-30)
      .attr("text-anchor", "middle")
      .style("font-size", "18px")
      .attr("fill", titleColor)
      .text((language === 'en')? "Month" : "月 份");
  svg.append("text")
      .attr("x", -200)
      .attr("y", height - padding * 4.2)
      .attr("text-anchor", "middle")
      .attr("transform", "rotate(-90)")
      .style("font-size", "18px")
      .attr("fill", titleColor)
      .text((language === 'en')? "Number" : yUnitTitle);

}

const dataURL = (location.search.indexOf('most=') >= 0) ? '/api/data/stats?most=1': '/api/data/stats';
//const dataURL = '/static/fake-data-stats.json'; // TODO!!
d3.json(dataURL).then( data => {
  // console.log(data);
  renderBarChart('#taibif-stats__this_year_occurrence', data['current_year']['occurrence']);
  renderBarChart('#taibif-stats__this_year_dataset', data['current_year']['dataset']);
  renderLineChart("#taibif-stats__trend_occurrence", data['history']['occurrence']);
  renderLineChart("#taibif-stats__trend_dataset", data['history']['dataset']);
})



//////////////////////////

function renderLineChart(selector, dataset) {
  //console.log(dataset);
  var svg = d3.select(selector).append("svg").attr("width", 1200).attr("height", height);

  var xScale = d3.scaleBand()
    .rangeRound([padding, width - padding])
    .padding(0.5)
      .domain(dataset.map(function(d) {  return d.year; }));

  var yScale = d3.scaleLinear()
    .domain([0, d3.max(dataset, function(d) { 
      // console.log(d.y2);
      return d.y2; })])
    .range([height - padding, padding]);

  svg.append("g")
    .attr("transform", "translate(" + 0 + "," + (height - padding) + ")")
    .attr("class", "axis")
    .call(d3.axisBottom(xScale));
  //const ticks = ();
  // console.log(dataset);
  if (selector == '#taibif-stats__trend_occurrence') {
    svg.append("g")
      .attr("transform", "translate(" + padding + "," + 0 + ")")
      .attr("class", "axis")
      .call(d3.axisLeft(yScale).ticks(5)
      .tickFormat(function (d) {
        switch(d) {
          case 1000000: return "1M"; break;
          case 2000000: return "2M"; break;
          case 3000000: return "3M"; break;
          case 4000000: return "4M"; break;
          case 5000000: return "5M"; break;
      }}));
  } else {
    svg.append("g")
      .attr("transform", "translate(" + padding + "," + 0 + ")")
      .attr("class", "axis")
      .call(d3.axisLeft(yScale).ticks(5));
  }

  let hackYSHIFT = 26;
  svg.append("path")
    .datum(dataset)
    .attr("fill", "none")
    .attr("stroke", colorSecondary)
    .style("stroke-dasharray", ("3, 3"))
    .attr("stroke-width", 3)
    .attr("d", d3.line()
          .x(function(d) { return xScale(d.year)+hackYSHIFT; })
          .y(function(d) { return yScale(d.y1); }));

  svg.append("path")
    .datum(dataset)
    .attr("fill", "none")
    .attr("stroke", "#846C5B")
    .attr("stroke-width", 3)
    .attr("d", d3.line()
          .x(function(d) { return xScale(d.year)+hackYSHIFT; })
          .y(function(d) { return yScale(d.y2); }));

  svg.append("g")
    .selectAll("path")
    .data(dataset)
    .enter()
    .append("text")
    .attr("x", function(d) {return xScale(d.year)+14; })
    .attr("y", function(d) {return yScale(d.y2)-20 })
    .text(function(d) {return d.y2.toLocaleString()})
    .attr("class", "label");

  svg.append("g")
    .selectAll("path")
    .data(dataset)
    .enter()
    .append("text")
    .attr("x", function(d) {return xScale(d.year)+24; })
    .attr("y", function(d) {return yScale(d.y1)-3; })
    .text(function(d) {return d.y1.toLocaleString()})
    .attr("fill", colorSecondary);
    //.attr("class", "label");
  const titleColor = colorPrimary;
  const appendixColor = colorPrimary;//'#1d5a91';
  const appendixColor2 = colorSecondary;//'#1d5a91';
  const yUnitTitle = (selector == '#taibif-stats__trend_occurrence') ? '筆  數' : '個  數';
  // add graph title
  svg.append("text")
     .attr("x", 500)
     .attr("y", height-30)
     .attr("text-anchor", "middle")
     .style("font-size", "18px")
     .attr("fill", titleColor)
     .text((language === 'en')? "Year" : "年 份");
  svg.append("text")
     .attr("x", -200)
     .attr("y", height - padding * 4.3)
     .attr("text-anchor", "middle")
     .attr("transform", "rotate(-90)")
     .attr("fill", titleColor)
     .text((language === 'en')? "Number" : yUnitTitle);
    
  const line1_desc = (language === 'en')? "━ Current accumulative" : "━ 目前累積筆數";
  const line2_desc = (language === 'en')? "┅ Current year accumulative" : "┅ 當年度累積筆數";
  
  svg.append("text")
     .attr("x", 900)
     .attr("y", 35)
     .attr("text-anchor", "left")
     .style("font-size", "18px")
     .attr("fill", appendixColor)
     .text(line1_desc);
  svg.append("text")
     .attr("x", 900)
     .attr("y", 65)
     .attr("text-anchor", "left")
     .style("font-size", "18px")
     .attr("fill", appendixColor2)
     .text(line2_desc);
}