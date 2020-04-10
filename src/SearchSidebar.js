import React, {useState, useRef} from 'react';
import Accordion from "./components/Accordion";
//import Tree from "./components/Tree";


function TreeNode({nodeData, onClickSpecies}) {
  //console.log('<TreeNode>', nodeData, onClickSpecies );
  const [isToggled, setToggleState] = useState(false);
  const [children, setChildrenState] = useState([]);

  //const node = useRef(null);
  // TODO: use useRef not to fetch every time toggle open
  //console.log('node:', nodeData);
  function toggleTreeNode(e) {

    setToggleState(isToggled === false ? true : false);
    if (isToggled) {
      setChildrenState([]);
    }
    else {
      const apiUrl = `/api/taxon/tree/node/${nodeData.id}`;
      fetch(apiUrl)
        .then(res => res.json())
        .then(
          (json) => {
            console.log('resp (tree): ', json);
            setChildrenState(json.children);

            // adjust Accordion content height
            const h = document.querySelector('.taxon-tree-container').scrollHeight;
            const contentEle = document.querySelector('.accordion-content-taxon');
            contentEle.style.maxHeight = `${h}px`;
          },
          (error) => {
            console.log('error tree click', error);
          });
    }
  }

  const childrenNodes = (children || []).map( child => {
    return <TreeNode key={child.id} nodeData={child} onClickSpecies={onClickSpecies} />
  });

  const node = (nodeData.data.rank === 'species') ?
        <div onClick={(e)=>onClickSpecies(e, nodeData.id, nodeData.data.name)} className="taxon-tree-node-item">{nodeData.data.name}</div> :
        <div onClick={toggleTreeNode} className="taxon-tree-node-item">{nodeData.data.name}</div> ;

  return (
      <div className="taxon-tree-node-wrapper">
      {node}
      {childrenNodes}
      </div>
  )
}

function Tree(props) {
  //console.log('<Tree> ', props);
  const treeRootNodes = props.taxonData.tree.map((child) => {
    return <TreeNode key={child.id} nodeData={child} onClickSpecies={props.onClickSpecies} />
  });

  return (
      <div className="taxon-tree-container">
      {treeRootNodes}
      </div>
  );
}
const SearchTaxon = (props) => {
  console.log('<SearchTaxon>', props);
  //const autocompleteItems = [];
  let suggestContainer = null;
  if (props.taxonData.suggestList.length > 0) {
    const autocompleteItems = props.taxonData.suggestList.map((t)=>{
      return <div className="search-taxon__suggest-item" key={t.id} onClick={(e)=>props.onSuggestClick(e, t.id, t.name)}>{t.name_full} ({t.name_zh})</div>
    });
    suggestContainer = (
      <div className="search-taxon__suggest-list">
      {autocompleteItems}
      </div>
    )
  }

  let checkedContainer = null;
  let speciesChecked = [];
  for (let tid in props.taxonData.checked) {
    const name = props.taxonData.checked[tid];
    speciesChecked.push(<div key={tid}><input type="checkbox" defaultChecked onClick={(e)=>{props.onTaxonRemoveClick(e, tid)}} /> {name}</div>);
  }
  if (speciesChecked.length > 0) {
    checkedContainer = (
        <div className="search-taxon__checked">
        {speciesChecked}
      </div>
    );
  }

  return (
      <div>
      <input className="form-control search-keyword" placeholder="搜尋學名" name="search_taxon" id="search-taxon-input" type="text" onChange={props.onTaxonKeywordChange} value={props.taxonData.queryKeyword}/>
      <div>
      {suggestContainer}
      </div>
      {checkedContainer}
      <Tree taxonData={props.taxonData} onClickSpecies={props.onTreeSpeciesClick} />
      </div>
  );
}

function SearchSidebar(props) {
  //console.log(props);
  const menuList = props.menus.map(function(m) {
    const menu_items = m.rows.map(function(x) {
      const itemChecked = props.filters.has(`${m.key}=${x.key}`);
      return (<div key={x.key} className="menu-item">
              <div className="menu-item__title">
              <input type="checkbox" onChange={(e)=> {e.persist(); props.onClick(e, m.key, x.key)}} checked={itemChecked} /> {x.label}
              </div>
              <div className="menu-item__count">
              {x.count}
              </div>
              </div>);
    });
    return (
        <Accordion key={m.key} title={m.label} content={menu_items} />
    )
  });
  const numFilters = props.filters.size === 0 ? '' : <span className="num-filters badge">{props.filters.size}</span>;
  let searchTypeLabel = '';
  let searchTaxonContainer = null;
  if (props.searchType === 'dataset') {
    searchTypeLabel = '資料集';
  }
  else if (props.searchType === 'occurrence') {
    searchTypeLabel = '出現紀錄';
    const scientificNameContent = <SearchTaxon {...props.taxonProps} />;
    searchTaxonContainer = <Accordion key="taxon" title="學名" content={scientificNameContent} appendClass="accordion-content-taxon" />;
  }
  else if (props.searchType === 'species') {
    searchTypeLabel = '物種';
  }
  else if (props.searchType === 'publisher') {
    searchTypeLabel = '發布者';
  }

  return (
      <div className="col-xs-6 col-md-3 search-sidebar">
      <div className="search-sidebar__title search-sidebar__title--head">
      <span>{searchTypeLabel}</span>
      <div className="clear-filters" data-toggle="tooltip" data-placement="left" title="清除" onClick={props.onClickClear}>
      {numFilters}
      <span className="glyphicon glyphicon-trash"></span>
      </div>
      </div>
      <div className="input-group">
      <input className="form-control search-keyword" placeholder="搜尋關鍵字" name="search-term" id="search-term" type="text" value={props.queryKeyword} onChange={props.onChangeKeyword} onKeyPress={props.onKeyPressKeyword}/>
      <div className="input-group-btn">
      <button className="btn btn-default search-keyword-sign" type="submit" onClick={props.onClickSubmitKeyword}><i className="glyphicon glyphicon-search"></i></button>
      </div>
      </div>
      {searchTaxonContainer}
      {menuList}
      </div>)
}

export default SearchSidebar;
