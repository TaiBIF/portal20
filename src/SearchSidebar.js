import React, {useState, useRef} from 'react';
//import Accordion from "./components/Accordion";
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

  const icon = (isToggled) ? '📂': '📁';
  /*const node = (nodeData.data.rank === 'species') ?
        <div onClick={(e)=>onClickSpecies(e, nodeData.id, nodeData.data.name)} className="taxon-tree-node-item">{nodeData.data.name} </div> :
        <div onClick={toggleTreeNode} className="taxon-tree-node-item">{icon} {nodeData.data.name}👉</div> ;*/

  return (
      <div className="taxon-tree-node-wrapper">
      <div><span onClick={toggleTreeNode} className="taxon-tree-node-item">{icon}</span> {nodeData.data.name} <span onClick={(e)=>onClickSpecies(e, nodeData.id, nodeData.data.name)}>👉 </span></div>
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
  //console.log('<SearchTaxon>', props);
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

function Accordion(props) {
  const [isOpen, setOpenState] = useState(false);

  const {content, onClick, filters} = props;

  const appendClass = (props.appendClass) ? ` ${props.appendClass}` : '';
  function toggleAccordion() {
    setOpenState(isOpen === false ? true : false);
  }

  const menuItems = content.rows.map((x) => {
    const count = (x.count) ? x.count.toLocaleString() : null;
    const itemChecked = filters.has(`${content.key}=${x.key}`);
    return (
        <div className="search-sidebar-checkbox-wrapper" key={x.key}>
          <label className="custom-input-ctn">
          <input type="checkbox" onChange={(e)=> {e.persist(); onClick(e, content.key, x.key)}} checked={itemChecked} />
          <span className="checkmark"></span>
          <span className="search-sidebar-count-group">
            <span className="name">{x.label}</span>
            <span className="count">{count}</span>
          </span>
          </label>
        </div>
    );
  });
  return (
    <React.Fragment>
    <div className="search-sidebar-accordion-wrapper">
      <div className="search-sidebar-accordion-title">
        <a href="#" aria-expanded={isOpen ? "true": "false"} onClick={toggleAccordion}>
        {content.label}
        </a>
      </div>
      { isOpen ?
      <div className="search-sidebar-accordion-content collapse in">
        {menuItems}
      </div>
    : null}
    </div>
    </React.Fragment>);
}

function SearchSidebar(props) {
  //console.log(props);

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

  /*
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
      </div>)*/
  return (
      <div className="search-sidebar">
        <div className="modal right fade modal-search-side-wrapper" id="flowBtnModal" tabIndex="-1" role="dialog">
          <div className="modal-dialog" role="document">
            <div className="modal-content">
              <div className="search-sidebar-header">
                <span>{searchTypeLabel}</span>
                <div className="search-sidebar-header-del" data-toggle="tooltip" data-placement="left" title="清除" onClick={props.onClickClear}>
                  {props.filters.size > 0 ? <span className="badge">{props.filters.size}</span> : null}
                  <span className="glyphicon glyphicon-trash"></span>
                </div>
              </div>
              <div className="input-group search-sidebar-header-kw">
                <input className="form-control" placeholder="搜尋關鍵字" name="search-term" id="search-term" type="text" value="" value={props.queryKeyword} onChange={props.onChangeKeyword} onKeyPress={props.onKeyPressKeyword} />
                <div className="input-group-btn">
                  <button className="btn" type="submit" onClick={props.onClickSubmitKeyword}>
                    <i className="glyphicon glyphicon-search"></i>
                  </button>
                </div>
              </div>
              {props.menus.map((m) => 
                (<Accordion key={m.key} content={m} onClick={props.onClick} filters={props.filters}/>)
               )}
            </div>
          </div>
        </div>
      </div>
  )
}

export default SearchSidebar;
