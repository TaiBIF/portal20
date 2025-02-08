const rankMap = {
    'taibif_kingdom': { zh: '界', en: 'KINGDOM' },
    'taibif_phylum': { zh: '門', en: 'PHYLUM' },
    'taibif_class': { zh: '綱', en: 'CLASS' },
    'taibif_order': { zh: '目', en: 'ORDER' },
    'taibif_family': { zh: '科', en: 'FAMILY' },
    'taibif_genus': { zh: '屬', en: 'GENUS' },
    'taibif_scientificName': { zh: '種', en: 'SPECIES' }
};

$(document).ready(function() {
    const currentUrl = window.location.href;
    const datasetId = currentUrl.split('/dataset/')[1]?.split('/')[0];

    $('.contact-name').on('click', function() {
        toggleAccordion($(this));
    });

    // 獲取初始物種數資料
    createTaxonTreeRoot(datasetId);

    // 獲取初始出現紀錄比數分布的資料
    createPlots(datasetId);

    $('#download-chart-as-image').on('click', function() {
        downloadCombinedJPEG(['year-barchart-container', 'month-barchart-container']);
    });
});

function toggleAccordion($element) {
    var $ul = $element.next('ul');
    var $icon = $element.find('.icon-toggle svg');
    
    $ul.toggleClass('d-none');

    if ($ul.hasClass('d-none')) {
        $icon.css('transform', 'rotate(0deg)');
    } else {
        $icon.css('transform', 'rotate(180deg)');
    }
}

function createTaxonTreeRoot(datasetId) {
    $('#taxon-tree-loader').removeClass('d-none');
    $.ajax({
        type: 'GET',
        url: '/api/get_dataset_taxon_tree_data',
        data: { dataset_id: datasetId },
        dataType: 'json',
        success: function (data) {
            if (data.root && Array.isArray(data.root)) {
                $('#taxon-tree-loader').addClass('d-none');
                const container = $('#tree-container');
    
                data.root.forEach(node => {
                    const rankInMandarin = rankMap[node.rank]?.zh;
                    const rankInEngUppercase = rankMap[node.rank]?.en;
                    const taxonNode = $(`
                        <div class="taxon-tree-wrapper">
                            <span class="myicon icon-triangle-right"></span>
                            <span class="taxon-tree-node">
                                <label>
                                    <div class="taxon-tree-rank">${rankInMandarin}</div>
                                    <div class="taxon-tree-rank-en">${rankInEngUppercase}</div>
                                    <div class="taxon-tree-name" data-rank="${node.rank}" data-name="${node.scientific_name}">
                                        <a href="/species/${node.taicol_taxon_id}" target="_blank">${node.scientific_name} ${node.name_zh}</a>
                                    </div>
                                    <div class="taxon-tree-count">${node.count}</div>
                                </label>
                            </span>
                            <div class="child-nodes" style="display: none; margin-left: 15px;"></div>
                        </div>
                    `);
    
                    taxonNode.find('.myicon').on('click', function () {
                        toggleNode(taxonNode, datasetId);
                    });
    
                    container.append(taxonNode);
                });
            } else {
                $('#taxon-tree-loader').addClass('d-none');
                alert('獲取資料發生錯誤');
            }
        }
    });
}

function toggleNode(taxonNode, datasetId) {
    $('#taxon-tree-loader').removeClass('d-none');
    $('#taxon-tree-loader-overlay').removeClass('d-none');
    const isToggled = taxonNode.find('.myicon').hasClass('icon-triangle-down');
    const childContainer = taxonNode.find('.child-nodes');
    const toggledItem = taxonNode.find('.taxon-tree-name');
    const rank = toggledItem.data('rank');
    const scientificName = toggledItem.data('name');

    // console.log(rank, scientificName);

    taxonNode.find('.myicon')
        .toggleClass('icon-triangle-down', !isToggled)
        .toggleClass('icon-triangle-right', isToggled);

    if (!isToggled) { // 展開下階層物種資訊時
        if (childContainer.children().length === 0) { // 還沒有內容，從後端 request
            $.ajax({
                type: 'GET',
                url: '/api/get_dataset_taxon_tree_data',
                data: { dataset_id: datasetId, parent_rank: rank, parent_name: scientificName },
                dataType: 'json',
                success: function (childData) {
                    $('#taxon-tree-loader').addClass('d-none');
                    $('#taxon-tree-loader-overlay').addClass('d-none');
                    // console.log(childData.node);
                    if (childData.node && Array.isArray(childData.node)) {
                        if (childData.node.length === 0){
                            alert('沒有更多下階層物種資訊');
                        }
                        childData.node.forEach(childNode => {
                            const rankInMandarin = rankMap[childNode.rank]?.zh;
                            const rankInEngUppercase = rankMap[childNode.rank]?.en;
                            const nameInMandarin = childNode.name_zh ? childNode.name_zh : ''
                            const childTaxonNode = $(`
                                <div class="dataset-taxon-tree-wrapper">
                                    ${childNode.rank !== 'taibif_scientificName' ? '<span class="myicon icon-triangle-right"></span>' : '<span class="icon-triangle-right-border"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="currentColor" class="bi bi-caret-right" viewBox="0 0 16 16"><path d="M6 12.796V3.204L11.481 8zm.659.753 5.48-4.796a1 1 0 0 0 0-1.506L6.66 2.451C6.011 1.885 5 2.345 5 3.204v9.592a1 1 0 0 0 1.659.753"/></svg></span>'}
                                    <span class="taxon-tree-node">
                                        <label>
                                            <div class="taxon-tree-rank">${rankInMandarin}</div>
                                            <div class="taxon-tree-rank-en">${rankInEngUppercase}</div>
                                            <div class="taxon-tree-name" data-rank="${childNode.rank}" data-name="${childNode.scientific_name}">
                                                ${
                                                    childNode.taicol_taxon_id 
                                                        ? `<a href="/species/${childNode.taicol_taxon_id}" target="_blank">${childNode.scientific_name} ${nameInMandarin}</a>` 
                                                        : `${childNode.scientific_name} ${nameInMandarin}`
                                                }
                                            </div>
                                            <div class="taxon-tree-count">${childNode.count}</div>
                                        </label>
                                    </span>
                                    <div class="child-nodes" style="display: none; margin-left: 15px;"></div>
                                </div>
                            `);

                            childTaxonNode.find('.myicon').on('click', function () {
                                toggleNode(childTaxonNode, datasetId);
                            });

                            childContainer.append(childTaxonNode);
                        });
                        childContainer.slideDown(); 
                    } else {
                        $('#taxon-tree-loader').addClass('d-none');
                        $('#taxon-tree-loader-overlay').addClass('d-none');
                        alert('獲取資料發生錯誤');
                    }
                }
            });
        } else { // 已經有內容，展開下階層物種資訊
            $('#taxon-tree-loader').addClass('d-none');
            $('#taxon-tree-loader-overlay').addClass('d-none');
            childContainer.slideDown();
        }
    } else { // 隱藏下階層物種資訊時
        $('#taxon-tree-loader').addClass('d-none');
        $('#taxon-tree-loader-overlay').addClass('d-none');
        childContainer.slideUp();
    }
}

function createPlots(datasetId) {
    $('#year-barchart-loader').removeClass('d-none');
    $('#year-barchart-loader-overlay').removeClass('d-none');
    $.ajax({
        type: 'GET',
        url: '/api/get_dataset_datetime_data',
        data: { dataset_id: datasetId },
        dataType: 'json',
        success: function (data) {
            $('#year-barchart-loader-overlay').addClass('d-none');
            if (data) {
                if (data.year && data.year.length > 0) {
                    createBarChart(data.year, 'year-barchart-container', '年份', 'taibif_year');
                } else {
                    $('#year-barchart-loader').addClass('d-none');
                    alert('獲取年份資料發生錯誤');
                }

                if (data.month && data.month.length > 0) {
                    createBarChart(data.month, 'month-barchart-container', '月份', 'taibif_month');
                } else {
                    $('#year-barchart-loader').addClass('d-none');
                    alert('獲取月份資料發生錯誤');
                }
            } else {
                $('#year-barchart-loader').addClass('d-none');
                alert('獲取資料發生錯誤');
            }
        }
    });
}

function createBarChart(data, containerID, xAxisLabel, searchParma) {
    const currentUrl = window.location.href;
    const datasetId = currentUrl.split('/dataset/')[1]?.split('/')[0];
    if (data && Array.isArray(data)) {
        $('#year-barchart-loader').addClass('d-none');
        // 設置寬、高及邊距
        const container = d3.select('.table-container');
        const margin = { top: 20, right: 70, bottom: 60, left: 70 };
        const containerWidth = container.node().getBoundingClientRect().width; // 父容器寬度
        const width = containerWidth - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;


        // 建立 SVG 容器
        const svg = d3.select(`#${containerID}`)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left}, ${margin.top})`);

        // 建立 X 軸和 Y 軸比例尺
        const x = d3.scaleBand()
            .domain(data.map(d => d.label))
            .range([0, width])
            .padding(0.1);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.count)])
            .range([height, 0]);

        const interval = Math.ceil(data.length / (width / 50)); // 每個標籤寬度約為 50px
        svg.append("g")
            .attr("class", "axis axis-x")
            .attr("transform", `translate(0, ${height})`)
            .call(
                d3.axisBottom(x)
                    .tickValues(
                        xAxisLabel === "月份" // 根據 xAxisLabel 判斷是否篩選
                            ? data.map(d => d.label) // 如果是月份，顯示所有標籤
                            : data.map((d, i) => (i % interval === 0 ? d.label : null)).filter(d => d) // 如果是年份，篩選部分標籤
                    )
            );

        // 添加 Y 軸
        svg.append("g")
            .attr("class", "axis axis-y")
            .call(d3.axisLeft(y));

        // 添加 X 軸標題
        svg.append("text")
            .attr("class", "axis-title")
            .attr("x", width / 2)
            .attr("y", height + 40) // 軸線下方一點
            .style("font-size", "12px")
            .attr("text-anchor", "middle")
            .text(xAxisLabel);

        // 創建 tooltip 元素
        const tooltip = d3.select("body").append("div")
        .attr("class", "barchart-tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("padding", "8px")
        .style("border-radius", "2px")
        .style("font-size", "12px");

        // 繪製條形圖
        svg.selectAll(".bar")
        .data(data)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.label))
        .attr("y", d => y(d.count))
        .attr("width", x.bandwidth())
        .attr("height", d => height - y(d.count))
        .on("mouseover", function(event, d) {
            const formattedCount = d.count.toLocaleString();
            tooltip.style("visibility", "visible")
                .text(`${xAxisLabel}: ${d.label} | 紀錄筆數: ${formattedCount}`)
        })
        .on("mousemove", function(event) {
            tooltip.style("top", (event.pageY + 10) + "px")
                .style("left", (event.pageX + 10) + "px");
        })
        .on("mouseout", function() {
            tooltip.style("visibility", "hidden");
        })
        .on("click", function (event, d) {
            const url = `/occurrence/search/?taibif_datasetKey=${datasetId}&${searchParma}=${d.label}`;
            window.location.href = url; // 跳轉到目標頁面
        });
    } else {
        $('#year-barchart-loader').addClass('d-none');
        alert('獲取資料發生錯誤');
    }
}

function downloadCombinedJPEG(containerIDs, outputFileName = "records_distribution_chart.jpg", scaleFactor = 2) {
    const svgNS = "http://www.w3.org/2000/svg";
    const serializer = new XMLSerializer();

    // 創建新 SVG 容器
    const combinedSVG = document.createElementNS(svgNS, "svg");
    combinedSVG.setAttribute("xmlns", "http://www.w3.org/2000/svg");

    let totalWidth = 0, maxHeight = 0, maxBottomPadding = 0;

    containerIDs.forEach((id, index) => {
        const svg = document.querySelector(`#${id} svg`);
        if (!svg) return;

        const clonedSVG = svg.cloneNode(true);
        const bbox = svg.getBoundingClientRect();  // 使用 getBoundingClientRect() 避免裁切
        const width = bbox.width;
        const height = bbox.height;

        // 計算 x 軸標籤的額外空間
        const axisText = svg.querySelector("text");
        if (axisText) {
            const axisBBox = axisText.getBoundingClientRect();
            maxBottomPadding = Math.max(maxBottomPadding, axisBBox.height);
        }

        if (index === 0) {
            maxHeight = height;
        } else {
            maxHeight = Math.max(maxHeight, height);
        }

        clonedSVG.setAttribute("x", totalWidth);
        clonedSVG.setAttribute("y", 0);

        combinedSVG.appendChild(clonedSVG);
        totalWidth += width;
    });

    // 增加 x 軸標籤的空間
    const finalHeight = maxHeight + maxBottomPadding + 10; // +10 避免邊界被裁切

    // 設定合併後的 SVG 大小
    combinedSVG.setAttribute("width", totalWidth);
    combinedSVG.setAttribute("height", finalHeight);
    combinedSVG.setAttribute("viewBox", `0 0 ${totalWidth} ${finalHeight}`);

    // 修正裁切問題：添加白色背景
    const rect = document.createElementNS(svgNS, "rect");
    rect.setAttribute("width", totalWidth);
    rect.setAttribute("height", finalHeight);
    rect.setAttribute("fill", "white");
    combinedSVG.insertBefore(rect, combinedSVG.firstChild);

    // 將 SVG 轉換為字串
    const source = serializer.serializeToString(combinedSVG);
    const svgBlob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    // 建立 Canvas
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // 提高解析度
    canvas.width = totalWidth * scaleFactor;
    canvas.height = finalHeight * scaleFactor;
    ctx.scale(scaleFactor, scaleFactor);

    // 建立 Image 來載入 SVG
    const img = new Image();
    img.onload = function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 填充白色背景，防止變黑
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 繪製 SVG 到 Canvas
        ctx.drawImage(img, 0, 0);

        // 轉換為 JPEG 並下載
        const jpegURL = canvas.toDataURL("image/jpeg", 1.0);
        const link = document.createElement("a");
        link.href = jpegURL;
        link.download = outputFileName;
        link.click();

        // 釋放記憶體
        URL.revokeObjectURL(url);
    };
    img.src = url;
}


