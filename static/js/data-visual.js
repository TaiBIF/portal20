const chartTypeMapping = { // 依照繪製的圖表決定路由
    'barchart': '/api/get_barchart_data',
    'heatmap': '/api/get_heatmap_data'
};
const axisMapping = { // 軸上預先排序好的值，也以防有些項目、分類缺失
    'taibif_basisOfRecord': ['材料實體', '保存標本', '化石標本', '活體標本', '人為觀測', '材料樣本', '機器觀測', '調查活動', '名錄/分類群', '出現紀錄', '文獻紀錄'],
    'taibif_kingdom': ['Animalia', 'Archaea', 'Bacteria', 'Chromista', 'Fungi', 'Plantae', 'Protozoa', 'Viruses'],
    'taibif_taxonGroup': ['Unknown', 'Others', 'Mammals', 'Birds', 'Amphibia', 'Reptiles', 'Fishes', 'Insects', 'Bacteria', 'Fungi', 'Plants']
};
let yearPagination = 0;
let countryPagination = 0;

$(document).ready(function() {
    $('#heatmap-variable').select2();
    $('#heatmap-group').select2();
    checkBtnStatus();

    $('#heatmap-variable').on('change', function() { // 觀測紀錄項目下拉選單改變
        checkBtnStatus();
        const {yAxisValue, xAxisValue} = checkSelectorValue()

        if (xAxisValue === null) { // 只選擇紀錄項目（Ｙ軸）且紀錄分類（X軸）為空的話，繪製長條圖
            fectchData('barchart', yAxisValue, null, yearPagination, countryPagination);
        } else { // 紀錄項目（Ｙ軸）以及紀錄分類（X軸）都有選擇的話，繪製熱力圖
            fectchData('heatmap', yAxisValue, xAxisValue, yearPagination, countryPagination);
        };
    });

    $('#heatmap-group').on('change', function() { // 觀測紀錄項目下拉選單改變
        checkBtnStatus();
        const {yAxisValue, xAxisValue} = checkSelectorValue()

        if (yAxisValue === null) {
            window.alert('請先選擇項目');
        };

        if (xAxisValue != null & yAxisValue != null) { // 紀錄項目（Ｙ軸）以及紀錄分類（X軸）都有選擇的話，繪製熱力圖
            fectchData('heatmap', yAxisValue, xAxisValue, yearPagination, countryPagination);
        } else if (xAxisValue === null & yAxisValue != null) { // 紀錄分類（X軸）為無的話，繪製長條圖
            fectchData('barchart', yAxisValue, null, yearPagination, countryPagination);
        };
    });

    $('#prev-btn').on('click', function() {
        yearPagination += 1;
        checkBtnStatus();
        triggerRenderPlot();
    });

    $('#next-btn').on('click', function() {
        yearPagination -= 1;
        checkBtnStatus();
        triggerRenderPlot();
    });

    $('#prev-country-btn').on('click', function() {
        countryPagination -= 1;
        checkBtnStatus();
        triggerRenderPlot();
    });

    $('#next-country-btn').on('click', function() {
        countryPagination += 1;
        checkBtnStatus();
        triggerRenderPlot();
    });
});

function checkSelectorValue() {
    /*
    取得目前下拉式選單中被選中的值
    */ 
    const yAxis = $('#heatmap-variable').select2('data');
    const xAxis = $('#heatmap-group').select2('data');
    const yAxisValue = yAxis[0].id ? yAxis[0].id : null;
    const xAxisValue = xAxis[0].id ? xAxis[0].id : null;

    return {yAxisValue, xAxisValue}
};

function triggerRenderPlot() {
    /*
    前十年、後十年按鈕點擊之後，重新繪製對應的圖表
    */ 
    const {yAxisValue, xAxisValue} = checkSelectorValue()
    if (xAxisValue === null) { // 紀錄分類（X軸）為空則表示只選擇擇紀錄項目（Ｙ軸），重新繪製長條圖
        if (yAxisValue === 'taibif_year') {
            fectchData('barchart', 'taibif_year', null, yearPagination, countryPagination);
        } else {
            fectchData('barchart', yAxisValue, null, yearPagination, countryPagination);
        }
    } else { // 若選擇雙軸，重新繪製熱力圖
        fectchData('heatmap', yAxisValue, xAxisValue, yearPagination, countryPagination);
    };
};

function checkBtnStatus() {
    /*
    若下拉式選單有選擇年份的話，顯示前十年、後十年的按鈕，
    若無則隱藏前十年、後十年的按鈕。
    後十年按鈕在圖表為當今年份時，會隱藏起來
    */ 
    const {yAxisValue, xAxisValue} = checkSelectorValue()
    if ((yAxisValue === 'taibif_year') || (xAxisValue === 'taibif_year')) {
        $('#chart-btn-container').removeClass('d-none');
    } else {
        $('#chart-btn-container').addClass('d-none');
    }

    if (yearPagination === 0) {
        $('#next-btn').addClass('d-none');
    } else {
        $('#next-btn').removeClass('d-none');
    };

    if ((yAxisValue === 'taibif_country') || (xAxisValue === 'taibif_country')) {
        $('#chart-country-btn-container').removeClass('d-none');
    } else {
        $('#chart-country-btn-container').addClass('d-none');
    }

    if (countryPagination === 0) {
        $('#prev-country-btn').addClass('d-none');
    } else {
        $('#prev-country-btn').removeClass('d-none');
    };
};

function getCurrentYear(yearPagination) {
    /*
    取得當今年份，以及繪製年份相關圖表時的起始年份與結束年份。
    一次以 10 年為一區間，取哪個區間則用 yearPagination 控制，
    yearPagination 為全域變數，紀錄當下為第幾個年份區間
    */
    const currentYear = new Date().getFullYear();
    const startYear = currentYear - 10 * (yearPagination + 1);
    const endYear = currentYear - 10 * yearPagination;

    return {startYear, endYear}
};

function fectchData(chartType, yAxis, xAxis, yearPagination, countryPagination) {
    const {startYear, endYear} = getCurrentYear(yearPagination);
    $('.loader').removeClass('d-none');
    const url = chartTypeMapping[chartType]
    $.ajax({
        type: 'GET',
        url: url,
        data: { yAxis: yAxis, xAxis: xAxis, startYear: startYear, endYear: endYear, countryPagination: countryPagination },
        dataType: 'json',
        success: function(data) {
            if (chartType === 'heatmap') {
                if (data.has_more_results) {
                    $('#next-country-btn').removeClass('d-none');
                } else {
                    $('#next-country-btn').addClass('d-none');
                }
                createHeatmap(data.data, yAxis, xAxis, yearPagination);
            } else {
                if (data.has_more_results) {
                    $('#next-country-btn').removeClass('d-none');
                } else {
                    $('#next-country-btn').addClass('d-none');
                }
                createBarchart(data.chart_data, yAxis, yearPagination);
            }
            $('.loader').addClass('d-none');
        }
    });
};

function createBarchart(data, yAxis, yearPagination) {
    // Clear the contents of the div
    d3.select("#my_dataviz").html("");

    const margin = {top: 50, right: 50, bottom: 50, left: 100},
    width = 1200 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

    // 固定的 x 軸和 y 軸的值
    let yAxisValues = axisMapping[yAxis] || Array.from(new Set(data.map(d => d.name)));
    if (yAxis === 'taibif_year') {
        const {startYear, endYear} = getCurrentYear(yearPagination);
        yAxisValues = d3.range(startYear, endYear + 1);
    }

    // Create SVG element inside the div
    const svg = d3.select("#my_dataviz").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const y = d3.scaleBand()
        .range([height, 0])
        .padding(0.1)
        .domain(yAxisValues);

    let x;
    if (yAxis === 'taibif_country') {
        x = d3.scaleLinear()
        .range([0, width])
        .domain([0, 30000000]);
    } else {
        x = d3.scaleLinear()
        .range([0, width])
        .domain([0, d3.max(data, d => d.value)]);
    }

    svg.selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("y", d => y(d.name))
        .attr("height", y.bandwidth())
        .attr("x", 0)
        .attr("width", d => x(d.value))
        .attr("fill", "#4A3E3A");
    
    svg.selectAll(".label")
        .data(data)
        .enter().append("text")
        .attr("class", "label")
        .attr("x", d => x(d.value) + 5)  // 將文字放在 bar 的右邊，稍微偏移
        .attr("y", d => y(d.name) + y.bandwidth() / 2 + 5)  // 垂直置中
        .text(d => d.value)
        .style("text-anchor", "start")
        .style("fill", '#525252')
        .style("font-size", "12px");  

    const yAxisGroup = svg.append("g")
        .call(d3.axisLeft(y).tickSize(5));

    // 自動換行處理
    yAxisGroup.selectAll("text")
        .style("font-size", "12px")
        .attr("dx", -10)
        .call(wrap, margin.left - 10);  // 呼叫wrap函數，控制換行寬度
    
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(5));

    // wrap function: 用來手動將長的標籤名稱換行
    function wrap(text, width) {
        text.each(function() {
            const textElement = d3.select(this);
            const words = textElement.text().split(/\s+/).reverse();  // 將標籤分成單字
            let word;
            let line = [];
            let lineNumber = 0;
            const lineHeight = 1.1; // 字行高度
            const y = textElement.attr("y");
            const dy = parseFloat(textElement.attr("dy")) || 0;
            let tspan = textElement.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", `${dy}em`);
            
            while (word = words.pop()) {
                line.push(word);
                tspan.text(line.join(" "));
                if (tspan.node().getComputedTextLength() > width) {
                    line.pop();
                    tspan.text(line.join(" "));
                    line = [word];
                    tspan = textElement.append("tspan").attr("x", 0).attr("y", y).attr("dy", `${++lineNumber * lineHeight + dy}em`).text(word);
                }
            }
        });
    }
};


function createHeatmap(data, yAxis, xAxis, yearPagination) {
    // Clear the contents of the div
    d3.select("#my_dataviz").html("");
    // 設定
    const margin = {top: 50, right: 50, bottom: 50, left: 100},
    width = 1200 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

    // 固定的 x 軸和 y 軸的值
    let xAxisValues = axisMapping[xAxis] || Array.from(new Set(data.map(d => d.group)));;
    let yAxisValues = axisMapping[yAxis] || Array.from(new Set(data.map(d => d.variable)));
    if (yAxis === 'taibif_year') {
        const {startYear, endYear} = getCurrentYear(yearPagination);
        yAxisValues = d3.range(startYear, endYear + 1);
    } else if (xAxis === 'taibif_year') {
        const {startYear, endYear} = getCurrentYear(yearPagination);
        xAxisValues = d3.range(startYear, endYear + 1);
    };

    // 創建 SVG 元素
    const svg = d3.select("#my_dataviz")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // 定義 x 軸和 y 軸
    const x = d3.scaleBand()
        .range([0, width])
        .domain(xAxisValues)
        .padding(0.05);

    const y = d3.scaleBand()
        .range([height, 0])
        .domain(yAxisValues)
        .padding(0.05);

    // 定義顏色比例尺
    const colorScale = d3.scaleQuantize()
        .range(["#FFE6D6", "#F5B9B2", "#E3A59D", "#8E5B53", "#4A3E3A"]) // 指定顏色分段，淺色前、深色後
        .domain([0, d3.max(data, d => d.count)]);

    // 繪製 x 軸和 y 軸
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(x));

    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y))
        .style("font-size", "12px");

    // 將數據轉換為熱力圖的格式
    const heatmapData = xAxisValues.flatMap(group =>
        yAxisValues.map(variable => {
            const entry = data.find(d => d.group === group && d.variable === variable);
            return {
                group,
                variable,
                count: entry ? entry.count : 0
            };
        })
    );

    // const zeroColor = "#C8FCEA"; 
    const zeroColor = "#FFF9F7"; 
    // const zeroColor = "#eee8e6"; 

    // 繪製 heatmap
    svg.selectAll()
        .data(heatmapData, d => d.variable + ':' + d.group)
        .enter()
        .append("rect")
        .attr("x", d => x(d.group))
        .attr("y", d => y(d.variable))
        .attr("width", x.bandwidth())
        .attr("height", y.bandwidth())
        .style("fill", d => d.count === 0 ? zeroColor : colorScale(d.count))

    // 添加標籤或提示
    svg.selectAll(".text")
        .data(heatmapData)
        .enter()
        .append("text")
        .attr("x", d => x(d.group) + x.bandwidth() / 2)
        .attr("y", d => y(d.variable) + y.bandwidth() / 2)
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .text(d => d.count)
        .style("fill", d => {
            // 根據底色決定文字顏色
            const fillColor = d.count === 0 ? zeroColor : colorScale(d.count);
            return fillColor === '#FFE6D6' || fillColor === '#F5B9B2' || d.count === 0 ? "black" : "white";
        })
        .style("font-size", "12px");
}

