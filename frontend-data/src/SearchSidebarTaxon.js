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
