import React, {useState} from 'react';


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
            //contentEle.style.maxHeight = `${h}px`;
          },
          (error) => {
            console.log('error tree click', error);
          });
    }
  }

  const childrenNodes = (children || []).map( child => {
    return <TreeNode key={child.id} nodeData={child} onClickSpecies={onClickSpecies} />
  });

  const icon = (isToggled) ? <span class="myicon icon-triangle-right"></span>: <span class="myicon icon-triangle-down"></span>;
  /*const node = (nodeData.data.rank === 'species') ?
        <div onClick={(e)=>onClickSpecies(e, nodeData.id, nodeData.data.name)} className="taxon-tree-node-item">{nodeData.data.name} </div> :
        <div onClick={toggleTreeNode} className="taxon-tree-node-item">{icon} {nodeData.data.name}👉</div> ;*/
  //<span onClick={(e)=>onClickSpecies(e, nodeData.id, nodeData.data.name, nodeData.data.rank)} style={{cursor:'pointer'}}>  </span

  return (
      <div className="taxon-tree-node-wrapper">
      {icon}
      <span onClick={toggleTreeNode} className="taxon-tree-node-item">{nodeData.data.name}</span> 
      {/* <button onClick={(e)=>onClickSpecies(e, nodeData.id, nodeData.data.name, nodeData.data.rank)} style={{cursor:'pointer',width:'20px', height:'20x',fontSize:'12px',padding:'0px',borderColor:'#eee'}} >+</button> */}
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
      {/*<input className="form-control search-keyword" placeholder="搜尋學名" name="search_taxon" id="search-taxon-input" type="text" onChange={props.onTaxonKeywordChange} value={props.taxonData.queryKeyword}/>*/}
      <div>
      {suggestContainer}
      </div>
      { (checkedContainer) ?
      <div style={{margin: '2px 10px',border:'1px dashed #aaaaaa',padding: '6px'}}>
      <span>篩選物種</span>
      {checkedContainer}
      </div>
        : null}
      <Tree taxonData={props.taxonData} onClickSpecies={props.onTreeSpeciesClick} />
      </div>
  );
}

export default SearchTaxon;
