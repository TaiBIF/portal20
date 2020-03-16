
var width = 980;
var height = 380;
var padding = 80;

function renderBarChart(selector, dataset) {

  var svg = d3.select(selector).append("svg").attr("width", width).attr("height", height);

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

  svg.append("g")
    .attr("transform", "translate(" + padding + "," + 0 + ")")
    .attr("class", "axis")
    .call(d3.axisLeft(yScale).ticks(8));

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
}

const dataURL = (location.search.indexOf('most=') >= 0) ? '/api/data/stats?most=1': '/api/data/stats';
d3.json(dataURL).then( data => {
  //console.log(data);
  renderBarChart('#taibif-stats__this_year_occurrence', data['current_year']['occurrence']);
  renderBarChart('#taibif-stats__this_year_dataset', data['current_year']['dataset']);
  renderLineChart("#taibif-stats__trend_occurrence", data['history']['occurrence']);
  renderLineChart("#taibif-stats__trend_dataset", data['history']['dataset']);
})



//////////////////////////

function renderLineChart(selector, dataset) {
  //console.log(dataset);
  var svg = d3.select(selector).append("svg").attr("width", width).attr("height", height);

  var xScale = d3.scaleBand()
    .rangeRound([padding, width - padding])
    .padding(0.5)
      .domain(dataset.map(function(d) {  return d.year; }));

  var yScale = d3.scaleLinear()
    .domain([0, d3.max(dataset, function(d) { return d.y2; })])
    .range([height - padding, padding]);

  svg.append("g")
    .attr("transform", "translate(" + 0 + "," + (height - padding) + ")")
    .attr("class", "axis")
    .call(d3.axisBottom(xScale));

  svg.append("g")
    .attr("transform", "translate(" + padding + "," + 0 + ")")
    .attr("class", "axis")
    .call(d3.axisLeft(yScale).ticks(8));

  let hackYSHIFT = 26;
  svg.append("path")
    .datum(dataset)
    .attr("fill", "none")
    .attr("stroke", "#bb998b")
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
    .attr("class", "label");
}
