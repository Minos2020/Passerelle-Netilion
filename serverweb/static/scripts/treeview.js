

let selectedElementUI = null;
let selectedElementObj = null;
let selectedFolder = null;

function createTree(account, bindingIndex) {
  
  const container = document.getElementById('treeview-container');
  container.innerHTML = ""; // reset
  const root = document.createElement('div');

  const selectButton = document.getElementById('select-button');

  selectButton.onclick = () => {
      selectObject(bindingIndex);
  };

  // Construire une map des assets et tags
  const assetsById = Object.fromEntries(account.assets.map(a => [a.id, a]));
  const tagsByAsset = {};
  account.instrumentations.forEach(tag => {
    tag.assets.forEach(assetId => {
      if (!tagsByAsset[assetId]) tagsByAsset[assetId] = [];
      tagsByAsset[assetId].push(tag);
    });
  });

  const tagsByNode = {};
  account.instrumentations.forEach(tag => {
    tag.nodes.forEach(nodeId => {
      if (!tagsByNode[nodeId]) tagsByNode[nodeId] = [];
      tagsByNode[nodeId].push(tag);
    });
  });

  // Noeuds par parent
  const nodesByParent = {};
  account.nodes.forEach(node => {
    const pid = node.parent_id || 'root';
    if (!nodesByParent[pid]) nodesByParent[pid] = [];
    nodesByParent[pid].push(node);
  });

  // Assets par node
  const assetsByNode = {};
  account.assets.forEach(asset => {
    asset.nodes.forEach(nodeId => {
      if (!assetsByNode[nodeId]) assetsByNode[nodeId] = [];
      assetsByNode[nodeId].push(asset);
    });
  });

  function buildNode(node) {
    const el = document.createElement('div');
    el.className = 'tree-node folder';
  
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = node.name;
    label.onclick = () => {
      
      if (selectedFolder) selectedFolder.classList.remove('selected');
        el.classList.add('selected');
        selectedFolder = el;
        // console.log('Selected folder :', node);
      el.classList.toggle('open');
    };
  
    const children = document.createElement('div');
    children.className = 'children';
  
    // Sous-noeuds
    (nodesByParent[node.id] || []).forEach(subNode => {
      children.appendChild(buildNode(subNode));
    });
  
    // Assets dans ce node
    (assetsByNode[node.id] || []).forEach(asset => {
      children.appendChild(buildAsset(asset));
    });

    // Tag dans ce noeud
    (tagsByNode[node.id] || []).forEach(tag => {
      children.appendChild(buildTag(tag));
    });
  
    // // Tags rattachés directement à ce node sans asset
    // data.instrumentations.forEach(tag => {
    //   if (tag.nodes.includes(node.id) && tag.assets.length === 0) {
    //     children.appendChild(buildTag(tag));
    //   }
    // });
  
    el.appendChild(label);
    el.appendChild(children);
    return el;
  }
  

  function buildAsset(asset) {
    // const hasTags = tagsByAsset[asset.id]?.length > 0;
    const el = document.createElement('div');
    el.className = `tree-node asset`;
  
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = asset.product_name + (asset.description ? ` (${asset.description})` : '');
  
    // if (hasTags) {
    //   label.onclick = () => el.classList.toggle('open');
    // } else {
      label.onclick = () => {
        if (selectedElementUI) selectedElementUI.classList.remove('selected');
        el.classList.add('selected');
        selectedElementUI = el;
        selectedElementObj = asset;
        // console.log('Selected object (asset) :', asset);
      };
    // }
  
    // const children = document.createElement('div');
    // children.className = 'children';
  
    // (tagsByAsset[asset.id] || []).forEach(tag => {
    //   const tagEl = buildTag(tag);
    //   children.appendChild(tagEl);
    // });
  
    el.appendChild(label);
    // if (hasTags) el.appendChild(children);
    return el;
  }
  

  function buildTag(tag) {
    const el = document.createElement('div');
    el.className = 'tree-node tag';

    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = tag.tag;

    label.onclick = () => {
      if (selectedElementUI) selectedElementUI.classList.remove('selected');
      el.classList.add('selected');
      selectedElementUI = el;
      selectedElementObj = tag;
      // console.log('Selected object (tag) :', tag); // ici tu peux faire un callback
    };

    el.appendChild(label);
    return el;
  }

  // Racine = nodes racines
  (nodesByParent['root'] || []).forEach(rootNode => {
    root.appendChild(buildNode(rootNode));
  });

  container.appendChild(root);
}

function selectObject (bindingIndex) {
  if (selectedElementUI && selectedElementObj){
    bindings[bindingIndex].netilion_binding_id = selectedElementObj.id;
    console.log(bindings);
    // console.log(selectedElementObj)
    console.log(selectedElementObj.product_name || selectedElementObj.tag)
    closeModal();
    document.getElementById(`binding-label-${bindingIndex}`).innerHTML = ""
  }
  else showNotification("Aucun objet sélectionné", "warning");
}
