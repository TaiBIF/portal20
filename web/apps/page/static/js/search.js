/**
 * modified via:
 * https://www.cssscript.com/folder-tree-json/
 */

/* globals Tree */
'use strict';

var tree = new Tree(document.getElementById('search-taxon-tree'));

const RANK_MAP = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'];

//tree.on('open', e => console.log('open', e));
tree.on('select', e => {
  //console.log('select', e.dataset);
  const taxonID = e.dataset.taxon_id;
  const taxonName = e.dataset.taxon_name;
  const taxonRank = e.dataset.taxon_rank;
  let url = document.location.href;
  if (url.indexOf('?')>= 0) {
    url = `${url}&${taxonRank}=${taxonName}`;
  }
  else {
    url = `${url}?${taxonRank}=${taxonName}`;
  }
  //alert('aoeu');
  //document.location.href = url;
  console.log('url', url);
});
tree.on('action', e => console.log('action', e));
tree.on('fetch', e => {
  const rank_index = RANK_MAP.findIndex( x => x === e.dataset.rank);
  const rank = RANK_MAP[rank_index+1];
  fetchTree(rank, e.dataset.taxon_id)
    .then(data => {
      for (let i of data.tree) {
        tree.folder({
          name_v: `${i['name_v']}: ${i['count']}`,
          name: i['name'],
          type: Tree.FOLDER,
          async: true,
          taxon_id: i['taxon_id'],
          rank: rank,
        }, e);
      }
      e.resolve();
    })
    .catch(err => {
      console.log('fetch err', err);
    });
});


async function fetchTree(rank, taxon_id='') {
  let apiURL = '/occurrence/taxon/tree/';
  if (rank !== 'kingdom') {
    apiURL += `?rank=${rank}&taxon_id=${taxon_id}`;
  }
  console.log('fetch:', apiURL);
  let response = await fetch(apiURL);
  let data = await response.json();
  //console.log('data', data);
  return data;
}

fetchTree('kingdom')
  .then(data => {
    let treeData = [];
    for (let i of data.tree) {
      treeData.push({
        name_v: `${i['name_v']} : ${i['count']}`,
        name: i['name'],
        type: Tree.FOLDER,
        async: true,
        taxon_id: i['taxon_id'],
        rank: 'kingdom'
      });
    }
    tree.json(treeData);
  });


/*
  const taxonTree  = document.getElementById('taxon-tree');

    var toggler = document.getElementsByClassName("get-tree");
  var i;
  for (i = 0; i < toggler.length; i++) {
    toggler[i].addEventListener("click", function() {
      this.parentElement.querySelector(".nested").classList.toggle("active");
      //this.classList.toggle("caret-down");
    });
  }

  function renderTree(eleTree, rank, taxon_id='') {
    console.log(rank, taxon_id);
    let apiURL = '/occurrence/taxon/tree/';
    if (rank !== 'kingdom') {
      apiURL += `?rank=${rank}&taxon_id=${taxon_id}`;
    }
    fetch(apiURL)
      .then(
        function(response) {
          console.log('fetch', apiURL);
          if (response.status !== 200) {
            console.log('[taxon] Ret: '+ response.status);
            return;
          }

          response.json().then(function(data) {
            for (let i of data['tree']) {
              if ( i['count'] > 0 ) {
                const item = document.createElement('li');
                const itemChildWrapper = document.createElement('ul');
                const itemLabel = document.createElement('span');
                const itemLabelText = document.createTextNode(`${i['name_v']}`);
                const className = `taxon-${i['taxon_id']}`;
                //nodec.classList = [className];
                //node.dataset.taxon_id = i['taxon_id'];
                //node.dataset.rank = 'phylum';
                //node.onclick = function(e) {
                //  console.log(e, e.target.dataset);
                //  renderTree(e.target, e.target.dataset.rank, e.target.dataset.taxon_id)
                //}//;
                //const badge = document.createElement('span');
                //badge.classList = ['uk-badge'];
                //const t = document.createTextNode(i['count']);
                //badge.appendChild(t);
                itemLabel.appendChild(itemLabelText);
                itemChildWrapper.appendChild(itemLabel);
                item.appendChild(itemChildWrapper);
                //node.appendChild(badge);
                eleTree.appendChild(item);
                
                //}
              }
            }
          });
        }
      )
      .catch(function(err) {
        console.log('[taxon] Fetch Error :-S', err);
      });
  }

  renderTree(taxonTree, 'kingdom')*/
//});
