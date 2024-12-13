var apiUrl = 'https://api.gbif.org/v1/literature/search?countriesOfCoverage=TW';
var words = [];

$(document).ready(function () {
    // Start fetching data for GBIF
    fetchData('gbif-case');

    $('#taibif-case-btn').on('click', function() {
        $('#taibif-case').removeClass('d-none');
        $('#taibif-case_wrapper').removeClass('d-none');
        $('#gbif-case').addClass('d-none');
        $('#gbif-case_wrapper').addClass('d-none');
        
        // Initialize DataTable for taibif-case if it hasn't been initialized yet
        if (!$.fn.DataTable.isDataTable('#taibif-case')) {
            fetchData('taibif-case');
        }
    });

    $('#gbif-case-btn').on('click', function() {
        $('#gbif-case').removeClass('d-none');
        $('#gbif-case_wrapper').removeClass('d-none');
        $('#taibif-case').addClass('d-none');
        $('#taibif-case_wrapper').addClass('d-none');
    });

    $('#to-article-search-story').on('click', function() {
        const url = $(this).data('url');
        window.location.href = url;
    });
});

function fetchData(tableId) {
    let apiUrl = tableId === 'gbif-case' ? 'https://api.gbif.org/v1/literature/search?countriesOfCoverage=TW' : '/article/data_case';
    let offset = 0;
    let limit = 100;
    let allData = [];
    $('.loader').removeClass('d-none');

    $.ajax({
        url: apiUrl,
        type: 'GET',
        data:  tableId === 'gbif-case' ? { offset: offset, limit: limit } : '',
        dataType: 'json',
        success: function(data) {
            // Append the fetched data
            allData = allData.concat(data.results.map(row => {
                let mediaContent = '';
            
                if (row.identifiers && row.identifiers.doi) {
                    mediaContent = `<a href="https://doi.org/${row.identifiers.doi}" target="_blank">${row.identifiers.doi}</a>`;
                }
                
                if (row.media && row.media.length > 0) {
                    // 如果已有 identifiers.doi，則不顯示 media，反之顯示 media
                    if (!mediaContent) {
                        mediaContent = row.media.map(media => {
                            return `<a href="${media.media_url}" target="_blank">${media.media_name}</a>`;
                        }).join(', ');
                    }
                }
            
                return [
                    row.year || '',
                    row.title || '',
                    row.literatureType || '',
                    mediaContent || '', 
                ];
            }));
            data.results.forEach(row => {
                const keywords = row.keywords || '';
                const topics = row.topics || '';
            
                words = words.concat(keywords, topics);
            });
            let totalRecords = data.count;

            // Check if more data needs to be fetched
            if (allData.length < totalRecords) {
                offset += limit;
                fetchData(tableId);
            } else {
                $('#' + tableId).DataTable({
                    data: allData,
                    columns: [
                        { title: "年份" },
                        { title: "名稱" },
                        { title: "案例類型" },
                        { title: "相關連結" }
                    ],
                    columnDefs: [
                        { targets: 0, width: '15%' }, // Year column width
                        { targets: 1, width: '60%' }, // Title column width
                        { targets: 2, width: '15%' }, // Literature Type column width
                        { targets: 3, width: '20%' }  // DOI column width
                    ],
                    order: [[0, 'desc']], // Sort year in descending order
                    language: {
                        paginate: {
                            previous: "<span class='myicon icon-arrow-left'></span>",
                            next: "<span class='myicon icon-arrow-right'></span>"
                        },
                        search: '搜尋關鍵字：',
                    }
                });

                if ($('#data_viz').children().length === 0) {
                    // Create a new instance of the word cloud visualization
                    var myWordCloud = wordCloud('#data_viz');
                    // Start cycling through the demo data
                    showNewWords(myWordCloud);
                }
                $('.loader').addClass('d-none');
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error('Error fetching data:', textStatus, errorThrown);
            $('.loader').addClass('d-none');
        }
    });
}

//Simple animated example of d3-cloud - https://github.com/jasondavies/d3-cloud
//Based on https://github.com/jasondavies/d3-cloud/blob/master/examples/simple.html

// Encapsulate the word cloud functionality
function wordCloud(selector) {

    var fill = d3.scale.category20();

    //Construct the word cloud's SVG element
    var svg = d3.select(selector).append("svg")
        .attr("width", 500)
        .attr("height", 500)
        .append("g")
        .attr("transform", "translate(250,250)");


    //Draw the word cloud
    function draw(words) {
        var cloud = svg.selectAll("g text")
                        .data(words, function(d) { return d.text; })

        //Entering words
        cloud.enter()
            .append("text")
            .style("font-family", "Impact")
            .style("fill", function(d, i) { return fill(i); })
            .attr("text-anchor", "middle")
            .attr('font-size', 1)
            .text(function(d) { return d.text; });

        //Entering and existing words
        cloud
            .transition()
                .duration(600)
                .style("font-size", function(d) { return d.size + "px"; })
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .style("fill-opacity", 1);

        //Exiting words
        cloud.exit()
            .transition()
                .duration(200)
                .style('fill-opacity', 1e-6)
                .attr('font-size', 1)
                .remove();
    }


    //Use the module pattern to encapsulate the visualisation code. We'll
    // expose only the parts that need to be public.
    return {

        //Recompute the word cloud for a new set of words. This method will
        // asycnhronously call draw when the layout has been computed.
        //The outside world will need to call this function, so make it part
        // of the wordCloud return value.
        update: function(words) {
            d3.layout.cloud().size([500, 500])
                .words(words)
                .padding(5)
                .rotate(function() { return ~~(Math.random() * 2) * 90; })
                .font("Impact")
                .fontSize(function(d) { return d.size; })
                .on("end", draw)
                .start();
        }
    }
}

//Prepare one of the sample sentences by removing punctuation,
// creating an array of words and computing a random size attribute.
function getWords() {
    // 將陣列打亂順序
    const shuffledWords = words
        .map(word => ({ word, sort: Math.random() })) // 為每個元素生成隨機值
        .sort((a, b) => a.sort - b.sort) // 按隨機值排序
        .map(({ word }) => word); // 提取原始單詞

    // 選取前 20 個元素
    const sampleWords = shuffledWords.slice(0, 20);
    
    return sampleWords
        .map(function(d) {
            // 移除標點符號並分割成單詞
            const cleanedWords = d
                .replace(/[!\.,:;\?]/g, '')
                .split(' ');

            // 為每個單詞創建一個對象，並計算隨機大小
            return cleanedWords.map(function(word) {
                return { text: word, size: 10 + Math.random() * 60 };
            });
        })
        .flat(); // 將結果展平為單一陣列
}

//This method tells the word cloud to redraw with a new set of words.
//In reality the new words would probably come from a server request,
// user input or some other source.
function showNewWords(vis, i) {
    i = i || 0;

    vis.update(getWords(i ++ % words.length))
    setTimeout(function() { showNewWords(vis, i + 1)}, 5000)
}

