(function () {
  'use strict';

  const DEFAULT_WIDTH = 980;
  const CHART_HEIGHT = 360;
  const COLOR_PRIMARY = '#846C5B';
  const COLOR_SECONDARY = '#BB998B';
  const LANGUAGE = 'zh-hant';
  const AXIS_TITLE_FONT_SIZE = 14;

  const MONTHS = function(value) {
    const number = toNumber(value);

    if (Math.abs(number) >= 1000000) {
      return `${(number / 1000000).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
    }

    if (Math.abs(number) >= 1000) {
      return `${(number / 1000).toLocaleString(undefined, { maximumFractionDigits: 0 })}K`;
    }

    return Number(number);
  };

  const TICKS_OCCURRENCE = {
    2000: '2K',
    4000: '4K',
    6000: '6K',
    8000: '8K',
    10000: '10K',
    1000000: '1M',
    2000000: '2M',
    3000000: '3M',
    4000000: '4M',
    5000000: '5M',
    6000000: '6M'
  };

  function toNumber(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }

  function formatAxisValue(value) {
    return Number(toNumber(value)).toLocaleString();
  }

  function formatTick(value) {
    const number = toNumber(value);
    const mappedValue = TICKS_OCCURRENCE[number];
    if (mappedValue) {
      return mappedValue;
    }

    if (Math.abs(number) >= 1000000) {
      return `${(number / 1000000).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
    }

    if (Math.abs(number) >= 1000) {
      return `${(number / 1000).toLocaleString(undefined, { maximumFractionDigits: 0 })}K`;
    }

    return number;
  }

  function findNearestDatumByX(points, xScale, xValue, xKey, pointXOffset) {
    if (!points.length) {
      return null;
    }

    const bandwidth = typeof xScale.bandwidth === 'function' ? xScale.bandwidth() : 0;
    const halfBand = bandwidth ? bandwidth / 2 : 0;
    let nearest = null;
    let minDistance = Infinity;
    const key = xKey || 'x';
    const getOffset = typeof pointXOffset === 'function'
      ? pointXOffset
      : function (d) {
          return halfBand;
        };

    for (let i = 0; i < points.length; i += 1) {
      const point = points[i];
      const pointX = xScale(point[key]) + getOffset(point);
      const distance = Math.abs(xValue - pointX);
      if (distance < minDistance) {
        minDistance = distance;
        nearest = point;
      }
    }

    return nearest;
  }

  function getMousePositionFromEvent(node) {
    if (!node) {
      return null;
    }

    if (typeof d3 !== 'undefined' && typeof d3.event !== 'undefined') {
      if (typeof d3.pointer === 'function') {
        return d3.pointer(d3.event, node);
      }

      if (typeof d3.mouse === 'function') {
        return d3.mouse(node);
      }
    }

    return null;
  }

  function addChartHoverLayer({
    svg,
    width,
    height,
    padding,
    points,
    xScale,
    yScale,
    xKey,
    pointXOffset,
    formatText,
    getY
  }) {
    const domainLeft = padding;
    const domainRight = width - padding;
    const domainTop = padding;
    const domainBottom = height - padding;
    const domainHeight = domainBottom - domainTop;
    if (domainRight <= domainLeft || domainHeight <= 0) {
      return;
    }

    const xAccessor = function (datum) {
      const baseX = xScale(datum[xKey]);
      const offset = pointXOffset ? pointXOffset(datum) : 0;
      return baseX + offset;
    };

    const tooltip = svg.append('g')
      .attr('class', 'chart-callout')
      .style('display', 'none');

    const tooltipBg = tooltip.append('path')
      .attr('fill', '#fff')
      .attr('stroke', 'rgba(74, 62, 58, 0.92)')
      .attr('stroke-width', 1)
      .attr('opacity', 1);

    const tooltipText = tooltip.append('text')
      .attr('font-size', '12px')
      .attr('font-family', 'inherit')
      .attr('fill', 'rgba(74, 62, 58, 0.92)')
      .style('pointer-events', 'none');

    svg.append('rect')
      .attr('class', 'chart-hover-overlay')
      .attr('x', domainLeft)
      .attr('y', domainTop)
      .attr('width', domainRight - domainLeft)
      .attr('height', domainBottom - domainTop)
      .attr('fill', 'transparent')
      .style('pointer-events', 'all')
      .on('mouseenter.chartTooltip mousemove.chartTooltip', function () {
        const pointer = getMousePositionFromEvent(this);
        if (!Array.isArray(pointer) || pointer.length !== 2) {
          return;
        }

        const xValue = pointer[0];
        const yValue = pointer[1];
        const datum = findNearestDatumByX(points, xScale, xValue, xKey, pointXOffset);
        if (!datum || yValue < domainTop || yValue > domainBottom || xValue < domainLeft || xValue > domainRight) {
          tooltip.style('display', 'none');
          return;
        }

        const lines = formatText(datum);
        const texts = Array.isArray(lines) ? lines : String(lines).split('\n');
        const pointX = xAccessor(datum);
        const pointY = typeof getY === 'function'
          ? getY(datum)
          : yScale(d3.max([toNumber(datum.y1), toNumber(datum.y2)]));
        const safePointY = typeof pointY === 'number' && Number.isFinite(pointY) ? pointY : yScale.range()[0];

        tooltip.style('display', null);
        tooltip.attr('transform', `translate(${pointX},${safePointY})`);

        const spans = tooltipText
          .selectAll('tspan')
          .data(texts, function (d) { return String(d); });

        spans.enter()
          .append('tspan')
          .merge(spans)
          .attr('x', 0)
          .attr('y', function (_, textIndex) { return `${textIndex * 1.1}em`; })
          .attr('font-weight', function (_, textIndex) { return textIndex ? null : 'bold'; })
          .text(function (textLine) { return textLine; });

        spans.exit().remove();

        const {
          y,
          width: textWidth,
          height: textHeight
        } = tooltipText.node().getBBox();
        tooltipText.attr('transform', `translate(${-textWidth / 2},${15 - y})`);
        const boxLeft = -textWidth / 2 - 10;
        const boxRight = textWidth / 2 + 10;
        const boxBottom = textHeight + 20;
        tooltipBg.attr('d', `M${boxLeft},5H${boxRight}V${boxBottom}H${boxLeft}Z`);
      })
      .on('mouseout.chartTooltip', function () {
        tooltip.style('display', 'none');
      });
  }

  function getChartSize(selector) {
    const container = document.querySelector(selector);
    const containerWidth = container && container.clientWidth ? container.clientWidth : DEFAULT_WIDTH;
    const width = Math.max(320, Math.floor(containerWidth || DEFAULT_WIDTH));

    return {
      width,
      height: CHART_HEIGHT,
      padding: Math.max(48, Math.min(80, Math.round(width * 0.08)))
    };
  }

  function createSvg(selector) {
    const size = getChartSize(selector);
    const svg = d3.select(selector)
      .append('svg')
      .attr('width', '100%')
      .attr('height', size.height)
      .attr('viewBox', `0 0 ${size.width} ${size.height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet');

    return {
      svg,
      width: size.width,
      height: size.height,
      padding: size.padding
    };
  }

  function addAxesForBar({ svg, width, height, padding, xScale, yScale, isOccurrence }) {
    svg.append('g')
      .attr('transform', `translate(0, ${height - padding})`)
      .attr('class', 'axis')
      .call(d3.axisBottom(xScale));

    const yAxis = isOccurrence
      ? d3.axisLeft(yScale).ticks(5).tickFormat(function (d) {
          return MONTHS(d);
        })
      : d3.axisLeft(yScale).ticks(5);

    svg.append('g')
      .attr('transform', `translate(${padding}, 0)`)
      .attr('class', 'axis')
      .call(yAxis);
  }

  function addBarTitles({ svg, width, height, padding, yUnit }) {
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height - 30)
      .attr('text-anchor', 'middle')
      .style('font-size', `${AXIS_TITLE_FONT_SIZE}px`)
      .attr('fill', COLOR_PRIMARY)
      .text(LANGUAGE === 'en' ? 'Month' : '月 份');

    svg.append('text')
      .attr('transform', `translate(${padding * 0.25}, ${height / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .attr('fill', COLOR_PRIMARY)
      .text(LANGUAGE === 'en' ? 'Number' : yUnit);
  }

  function addLineTitles({ svg, width, height, padding, yUnit, selector }) {
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height - 30)
      .attr('text-anchor', 'middle')
      .style('font-size', `${AXIS_TITLE_FONT_SIZE}px`)
      .attr('fill', COLOR_PRIMARY)
      .text(LANGUAGE === 'en' ? 'Year' : '年 份');

    svg.append('text')
      .attr('transform', `translate(${padding * 0.25}, ${height / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .attr('fill', COLOR_PRIMARY)
      .text(LANGUAGE === 'en' ? 'Number' : yUnit);

    const line1 = LANGUAGE === 'en'
      ? '━ Current accumulative'
      : '┅ 當年度累積筆數';
    const line2 = LANGUAGE === 'en'
      ? '┅ Current year accumulative'
      : '━ 目前累積筆數';
    const legendX = padding + 8;
    const legendFontSize = AXIS_TITLE_FONT_SIZE;

    svg.append('text')
      .attr('x', legendX)
      .attr('y', 35)
      .attr('text-anchor', 'start')
      .style('font-size', `${legendFontSize}px`)
      .attr('fill', selector.includes('occurrence') ? COLOR_PRIMARY : COLOR_SECONDARY)
      .text(line1);

    svg.append('text')
      .attr('x', legendX)
      .attr('y', 65)
      .attr('text-anchor', 'start')
      .style('font-size', `${legendFontSize}px`)
      .attr('fill', selector.includes('occurrence') ? COLOR_SECONDARY : COLOR_PRIMARY)
      .text(line2);
  }

  function renderBarChart(selector, dataset) {
    const points = Array.isArray(dataset) ? dataset : [];
    if (!points.length) {
      return;
    }

    const isOccurrence = selector === '#taibif-stats__this_year_occurrence';
    const chart = createSvg(selector);
    const { svg, width, height, padding } = chart;

    const xScale = d3.scaleBand()
      .rangeRound([padding, width - padding])
      .padding(0.5)
      .domain(points.map(function (d) { return d.x; }));

    const yMax = d3.max(points, function (d) { return toNumber(d.y); });
    const yScale = d3.scaleLinear()
      .domain([0, (yMax || 0) + (isOccurrence ? 100000 : 5)])
      .range([height - padding, padding]);

    addAxesForBar({
      svg,
      width,
      height,
      padding,
      xScale,
      yScale,
      isOccurrence
    });

    const bars = svg.append('g')
      .selectAll('rect')
      .data(points)
      .enter()
      .append('rect')
      .attr('x', function (d) { return xScale(d.x); })
      .attr('y', function (d) { return yScale(toNumber(d.y)); })
      .attr('width', xScale.bandwidth())
      .attr('height', function (d) {
        return height - padding - yScale(toNumber(d.y));
      })
      .attr('fill', COLOR_PRIMARY);

    bars
      .append('title')
      .text(function (d) {
        return `${d.x} 月份：${formatAxisValue(d.y)} 筆數`;
      });

    addChartHoverLayer({
      svg,
      width,
      height,
      padding,
      points,
      xScale,
      xKey: 'x',
      yScale,
      pointXOffset: function () {
        return xScale.bandwidth() / 2;
      },
      formatText: function (datum) {
        return `${datum.x} 月份：${formatAxisValue(datum.y)} 筆數`;
      },
      getY: function (datum) {
        return yScale(toNumber(datum.y));
      }
    });

    addBarTitles({
      svg,
      width,
      height,
      padding,
      yUnit: isOccurrence ? '筆  數' : '個  數'
    });
  }

  function addLineSeries(svg, points, xScale, yScale, valueKey, color, selector, xOffset) {
    const offset = typeof xOffset === 'function' ? xOffset : function () { return 0; };
    const line = d3.line()
      .x(function (d) { return xScale(d.year) + offset(d); })
      .y(function (d) { return yScale(toNumber(d[valueKey])); });

    svg.append('path')
      .datum(points)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 3)
      .attr('stroke-dasharray', valueKey === 'y1' ? '3, 3' : null)
      .attr('d', line);

    const circles = svg.append('g')
      .selectAll(`circle.${valueKey}`)
      .data(points)
      .enter()
      .append('circle')
      .attr('cx', function (d) { return xScale(d.year) + offset(d); })
      .attr('cy', function (d) { return yScale(toNumber(d[valueKey])); })
      .attr('r', 4)
      .attr('fill', color);

    circles
      .append('title')
      .text(function (d) {
        const total = formatAxisValue(d[valueKey]);
        return `${d.year} 年份\n${valueKey === 'y2' ? '目前累積筆數' : '當年度累積筆數'}：${total}`;
      });
  }

  function renderLineChart(selector, dataset) {
    const points = Array.isArray(dataset) ? dataset : [];
    if (!points.length) {
      return;
    }

    const isOccurrence = selector === '#taibif-stats__trend_occurrence';
    const chart = createSvg(selector);
    const { svg, width, height, padding } = chart;

    const xScale = d3.scaleBand()
      .rangeRound([padding, width - padding])
      .padding(0.5)
      .domain(points.map(function (d) { return d.year; }));

    const yPrimaryMax = d3.max(points, function (d) { return toNumber(d.y2); });
    const ySecondaryMax = d3.max(points, function (d) { return toNumber(d.y2); });
    const yScalePrimary = d3.scaleLinear()
      .domain([0, (yPrimaryMax || 0) + 9000])
      .range([height - padding, padding]);
    const yScaleSecondary = d3.scaleLinear()
      .domain([0, (ySecondaryMax || 0) + 10])
      .range([height - padding, padding]);
    const yValueScale = isOccurrence ? yScalePrimary : yScaleSecondary;

    svg.append('g')
      .attr('transform', `translate(0, ${height - padding})`)
      .attr('class', 'axis')
      .call(d3.axisBottom(xScale));

    const yAxis = isOccurrence
      ? d3.axisLeft(yScalePrimary).ticks(5).tickFormat(formatTick)
      : d3.axisLeft(yScaleSecondary).ticks(5);

    svg.append('g')
      .attr('transform', `translate(${padding}, 0)`)
      .attr('class', 'axis')
      .call(yAxis);

    const lineXOffset = function () {
      return xScale.bandwidth() / 2;
    };

    addLineSeries(svg, points, xScale, yValueScale, 'y1', COLOR_SECONDARY, selector, lineXOffset);
    addLineSeries(svg, points, xScale, yValueScale, 'y2', COLOR_PRIMARY, selector, lineXOffset);

    addChartHoverLayer({
      svg,
      width,
      height,
      padding,
      points,
      xScale,
      yScale: yValueScale,
      xKey: 'year',
      pointXOffset: function () {
        return xScale.bandwidth() / 2;
      },
      formatText: function (datum) {
        const y1 = formatAxisValue(datum.y1);
        const y2 = formatAxisValue(datum.y2);
        return [
          `${datum.year} 年份`,
          `當年度累積筆數：${y1}`,
          `目前累積筆數：${y2}`
        ];
      },
      getY: function (datum) {
        return yValueScale(toNumber(datum.y2));
      }
    });

    addLineTitles({
      svg,
      width,
      height,
      padding,
      yUnit: isOccurrence ? '筆  數' : '個  數',
      selector
    });
  }

  const dataURL = (location.search.indexOf('most=') >= 0)
    ? '/api/data/stats?most=1'
    : '/api/data/stats';

  d3.json(dataURL)
    .then(function (data) {
      renderBarChart('#taibif-stats__this_year_occurrence', data.current_year.occurrence);
      renderBarChart('#taibif-stats__this_year_dataset', data.current_year.dataset);
      renderLineChart('#taibif-stats__trend_occurrence', data.history.occurrence);
      renderLineChart('#taibif-stats__trend_dataset', data.history.dataset);
    })
    .catch(function (error) {
      // 靜默失敗，保留現有頁面不阻斷渲染流程
      console.error('資料統計 API 讀取失敗：', error);
    });
})();
