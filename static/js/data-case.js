var apiUrl = 'https://api.gbif.org/v1/literature/search?countriesOfCoverage=TW';

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
            console.log(data);
            // Append the fetched data
            allData = allData.concat(data.results.map(row => [
                row.year || '',
                row.title || '',
                row.literatureType || '',
                (row.identifiers && row.identifiers.doi) ? `<a href="https://doi.org/${row.identifiers.doi}" target="_blank">${row.identifiers.doi}</a>` : ''
            ]));
            let totalRecords = data.count;

            // Check if more data needs to be fetched
            if (allData.length < totalRecords) {
                offset += limit;
                fetchData(tableId);
            } else {
                // Initialize DataTables once all data is fetched
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
                    order: [[0, 'desc']] // Sort year in descending order
                });
            }
            $('.loader').addClass('d-none');
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error('Error fetching data:', textStatus, errorThrown);
            $('.loader').addClass('d-none');
        }
    });
}
