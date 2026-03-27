var apiUrl = 'https://api.gbif.org/v1/literature/search?countriesOfCoverage=TW';
var words = [];

$(document).ready(function () {
    // Start fetching data for GBIF
    fetchData('gbif-case');

    $('#taibif-case-btn').on('click', function() {
        $('#taibif-case-btn').addClass('is-active');
        $('#gbif-case-btn').removeClass('is-active');
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
        $('#gbif-case-btn').addClass('is-active');
        $('#taibif-case-btn').removeClass('is-active');
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

                const taibifCaseTitle = `<a href="${row.article_url}">${row.title}</a>`
                const caseTitle = tableId === 'gbif-case' ? row.title : taibifCaseTitle
            
                return [
                    row.year || '',
                    caseTitle || '',
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
    if (!d3.layout || typeof d3.layout.cloud !== 'function') {
        console.error('d3-cloud is not loaded; skip rendering word cloud');
        return { update: function() {} };
    }
    var CLOUD_WIDTH = 500;
    var CLOUD_HEIGHT = 300;

    var palette = [
        '#846c5b', '#bb998b', '#4a3e3a', '#6b5a51', '#8a7b73',
        '#5f5551', '#d0c1b8', '#7d8f69', '#4f6f52', '#9a7f3f',
        '#3e6b8a', '#7a5f9e', '#b56f5d', '#5d8f88', '#a15b7a',
        '#6f6f6f', '#8f8179', '#a8b07f', '#6b8ea7', '#9c8b6c'
    ];
    var fill = function(i) {
        return palette[i % palette.length];
    };

    //Construct the word cloud's SVG element
    var svg = d3.select(selector).append("svg")
        .attr("width", CLOUD_WIDTH)
        .attr("height", CLOUD_HEIGHT)
        .append("g")
        .attr("transform", "translate(" + (CLOUD_WIDTH / 2) + "," + (CLOUD_HEIGHT / 2) + ")");


    //Draw the word cloud
    function draw(words) {
        var cloud = svg.selectAll("g text")
                        .data(words, function(d) { return d.text; })

        //Entering words
        var cloudEnter = cloud.enter()
            .append("text")
            .style("font-family", "Impact")
            .style("fill", function(d, i) { return fill(i); })
            .attr("text-anchor", "middle")
            .attr('font-size', 1)
            .text(function(d) { return d.text; });

        // 讓新加入的詞也套用 layout 計算後的位置與字級，避免卡在中心 (0,0)
        cloudEnter
            .transition()
                .duration(600)
                .style("font-size", function(d) { return d.size + "px"; })
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .style("fill-opacity", 1);

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
            var targetCount = words.length;
            var scaleSteps = [1, 0.9, 0.8, 0.72, 0.65, 0.58];
            var minFontSize = 9;

            function runAttempt(stepIndex) {
                var scale = scaleSteps[Math.min(stepIndex, scaleSteps.length - 1)];
                var attemptWords = words.map(function(w) {
                    return {
                        text: w.text,
                        size: Math.max(minFontSize, Math.round(w.size * scale))
                    };
                });

                d3.layout.cloud().size([CLOUD_WIDTH, CLOUD_HEIGHT])
                    .words(attemptWords)
                    .padding(stepIndex >= 2 ? 4 : 6)
                    .rotate(function() { return 0; })
                    .font("Impact")
                    .fontSize(function(d) { return d.size; })
                    .on("end", function(placedWords) {
                        if (placedWords.length < targetCount && stepIndex < scaleSteps.length - 1) {
                            runAttempt(stepIndex + 1);
                            return;
                        }
                        draw(placedWords);
                    })
                    .start();
            }

            runAttempt(0);
        }
    }
}

//Prepare one of the sample sentences by removing punctuation,
// creating an array of words and computing a random size attribute.
function getWords() {
    const tokenPool = words
        .flatMap(function(entry) {
            if (entry === null || entry === undefined) {
                return [];
            }

            const raw = String(entry);
            return raw
                .replace(/[!\.,:;\?\(\)\[\]\/]/g, ' ')
                .split(/[\s,，、|]+/)
                .map(function(token) { return token.trim(); })
                .filter(function(token) { return token.length > 0; });
        });

    // 去重，避免 d3 以 text 作為 key 時把重複詞合併掉
    const uniqueTokens = Array.from(new Set(tokenPool));

    if (uniqueTokens.length === 0) {
        return [];
    }

    // 先打亂，再取前 20 個（不重複）
    const shuffled = uniqueTokens
        .map(function(word) { return { word: word, sort: Math.random() }; })
        .sort(function(a, b) { return a.sort - b.sort; })
        .map(function(item) { return item.word; });

    return shuffled.slice(0, 20).map(function(word) {
        return { text: word, size: 12 + Math.random() * 24 };
    });
}

//This method tells the word cloud to redraw with a new set of words.
//In reality the new words would probably come from a server request,
// user input or some other source.
function showNewWords(vis, i) {
    i = i || 0;

    vis.update(getWords(i ++ % words.length))
    setTimeout(function() { showNewWords(vis, i + 1)}, 5000)
}
