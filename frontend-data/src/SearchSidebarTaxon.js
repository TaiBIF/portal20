import React, {useState} from 'react';


function TreeNode({nodeData, onClickSpecies, showLinnaeanOnly, treeKey, onTaxonRemoveClick}) {
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
      const apiUrl = `/api/taxon/tree/node/${nodeData.id}?linnaean=yes`;
        fetch(apiUrl)
          .then(res => res.json())
          .then(
            (json) => {
              console.log('resp (tree): ', json);
              setChildrenState(json.children);
            },
            (error) => {
              console.log('error tree click', error);
            });
    }
  }

  const childrenNodes = (children || []).map( child => {
    return <TreeNode key={child.id} nodeData={child} onClickSpecies={onClickSpecies} 
    treeKey={treeKey}
    />
  });

  const handleFilterState = (isChecked, e, tid) => {
    if(isChecked === true) {
      onTaxonRemoveClick(e, tid);
    }
  };

  return (
      <div className="taxon-tree-node-wrapper">
          <span className={`myicon ${isToggled ? 'icon-triangle-down' : 'icon-triangle-right'}`} 
                onClick={toggleTreeNode}>
          </span>
          <span className='taxon-tree-node-item'>
            {/* <input type='checkbox' id='check1' checked={isChecked} onChange={handleCheckboxState} onClick={(e) => {
              onClickSpecies(e, nodeData.id, nodeData.data.name, nodeData.data.rank);
              handleFilterState(isChecked, e, nodeData.id);
            }}></input> */}
            <label className='form-check-label' onClick={(e) => onClickSpecies(e, nodeData.id, nodeData.data.name, nodeData.data.rank)}>
              <span className='taxon-tree-rank'>{nodeData.data.rank}</span>
              <span className='taxon-tree-name'>{nodeData.data.name}</span>
            </label>
          </span>
          {childrenNodes}
      </div>
  )
}

function Tree(props) {
  const [treeKey, setTreeKey] = useState(Date.now());

  const handleCheckboxChange = () => {
    // Update the state in the Tree component
    setShowLinnaeanOnly((prev) => !prev);
    const newTreeKey = Date.now();
    setTreeKey(newTreeKey);
  };
  //console.log('<Tree> ', props);
  const treeRootNodes = props.taxonData.tree.map((child) => {
    return <TreeNode key={child.id} nodeData={child} onClickSpecies={props.onClickSpecies} 
    onTaxonRemoveClick={props.onTaxonRemoveClick}
    treeKey={treeKey}/>
  });

  return (
      <div className="taxon-tree-container">
        <div className="taxon-tree-title">
          <span> 
          </span>
        </div>
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
      <div className='taxon-tree-wrapper'>
        <div className="icon-container">
          <div className="tooltip-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#846c5b" viewBox="0 0 24 24">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
              <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0"/>
            </svg>
          </div>
          <div className="tooltip-context">此物種樹只收錄包含在物種出現紀錄中，且對應到 TaiCOL 的物種</div>
        </div>
      {/*<input className="form-control search-keyword" placeholder="搜尋學名" name="search_taxon" id="search-taxon-input" type="text" onChange={props.onTaxonKeywordChange} value={props.taxonData.queryKeyword}/>*/}
      <div>
      {suggestContainer}
      </div>
      { (checkedContainer) ?
      // <div style={{margin: '2px 10px',border:'1px dashed #aaaaaa',padding: '6px'}}>
      <div className='selected-box'>
      <span>篩選物種</span>
      {checkedContainer}
      </div>
        : null}
      <Tree taxonData={props.taxonData} onClickSpecies={props.onTreeSpeciesClick}/>
      </div>
  );
}

export default SearchTaxon;
