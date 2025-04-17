

let selectedElementUI = null;
let selectedElementObj = null;
let selectedParent = null;

function createTree(account, bindingIndex) {
  
  const container = document.getElementById('treeview-container');
  container.innerHTML = ""; // reset
  const root = document.createElement('div');

  const selectButton = document.getElementById('select-button');

  selectButton.onclick = () => {
      selectObject(bindingIndex);
  };

  // Construire des map d'assets, de tags
  const assetsByTag = {};
  account.assets.forEach(asset => {
    asset.instrumentations.forEach(tagId => {
      if (!assetsByTag[tagId]) assetsByTag[tagId] = [];
      assetsByTag[tagId].push(asset);
    });
  });
  // console.log(assetsByTag)

  // const assetsByTag2 = {};
  // account.instrumentations.forEach(tag => {
  //   tag.assets.forEach(assetID => {
  //     if (!assetsByTag2[assetID]) assetsByTag2[assetID] = [];
  //     assetsByTag2[assetID].push(tag);
  //   });
  // });
  // console.log(assetsByTag2)

  // tags par Noeud
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

  // tags hors d'un node
  const tagsWithoutNode = [];
  account.instrumentations.forEach(tag => {
    if (!tag.nodes.length > 0) tagsWithoutNode.push(tag);
  });
  console.log(tagsWithoutNode)
  // assets hors d'un node
  const assetsWithoutNode = [];
  account.assets.forEach(asset => {
    if (!asset.nodes.length > 0) assetsWithoutNode.push(asset);
  });
  console.log(assetsWithoutNode)


  function buildNode(node) {
    const el = document.createElement('div');
    el.className = 'tree-node folder';
  
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = node.name;
    label.onclick = () => {
      
      if (el.className.includes('selected open') || el.className.includes('open')){
        if (selectedParent) selectedParent.classList.remove('selected'); selectedParent = null;
      } 
      else if (selectedParent) {
        selectedParent.classList.remove('selected');
        el.classList.add('selected');
        selectedParent = el;
      }
      else {
        el.classList.add('selected');
        selectedParent = el;
        el.get
      }
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
  
    const label = document.createElement('div');
    label.className = 'label';
    label.style.fontSize = '1em';
    label.innerHTML = `
    <div>
      ${asset.product_name} - ${asset.serial_number ? '['+asset.serial_number+']' : ""}
    </div>
    <div>
    <i>${asset.description ? '('+asset.description+')' : ""}</i>
    </div>
    `;
  
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

    el.appendChild(label);
    // if (hasTags) el.appendChild(children);
    return el;
  }
  

  function buildTag(tag) {
    const el = document.createElement('div');
    el.className = 'tree-node tag';

    const label = document.createElement('span');
    label.className = 'label';
    label.style.fontSize = '1em';
    label.innerHTML = `${tag.tag} <i>${tag.description ? '('+tag.description+')' : ""}</i>`;

    label.onclick = () => {
      if (el.className.includes('selected open') || el.className.includes('open')){
        if (selectedParent) selectedParent.classList.remove('selected'); selectedParent = null;
      } 
      else if (selectedParent) {
        selectedParent.classList.remove('selected');
        el.classList.add('selected');
        selectedParent = el;
      }
      else {
        el.classList.add('selected');
        selectedParent = el;
        el.get
      }
      
      el.classList.toggle('open');
      // console.log('Selected object (tag) :', tag); // ici tu peux faire un callback
    };

    const children = document.createElement('div');
    children.className = 'children';

    // Assets dans ce node
    (assetsByTag[tag.id] || []).forEach(asset => {
      children.appendChild(buildAsset(asset));
    });

    el.appendChild(label);
    el.appendChild(children);
    return el;
  }

  // Racine = nodes racines
  (nodesByParent['root'] || []).forEach(rootNode => {
    root.appendChild(buildNode(rootNode));
  });

  tagsWithoutNode.forEach(tag => {
    root.appendChild(buildTag(tag));
  });

  assetsWithoutNode.forEach(asset => {
    root.appendChild(buildAsset(asset));
  });

  container.appendChild(root);
}

function selectObject (bindingIndex) {
  if (selectedElementUI && selectedElementObj){
    bindings[bindingIndex].netilion_binding_id = selectedElementObj.id;
    
    if(selectedElementObj.tag){
      document.getElementById(`binding-label-${bindingIndex}`).innerHTML = `
        <div class="asset-tag-header">${'🏷️'+selectedElementObj.tag}</div>
        <div class="asset-tag-info"><i>${'<b>SN : </b> \n'+selectedElementObj.description, selectedElementObj.description != null ? selectedElementObj.description : "No description"}</i></div>
        `;
    } else if (selectedElementObj.product_name) {
      document.getElementById(`binding-label-${bindingIndex}`).innerHTML = `
        <div class="asset-tag-header">${'📍'+selectedElementObj.product_name}</div>
        <div class="asset-tag-info">${'<b>SN : </b> \n'+selectedElementObj.serial_number}</div>
        <div class="asset-tag-info"><i>${selectedElementObj.description, selectedElementObj.description != null ? selectedElementObj.description : "No description"}</i></div>
        `;
    }
    // Désactive l'affichage de la fenêtre de choix et réinitialise les variables
    selectedElementUI = null;
    selectedElementObj = null;
    selectedParent = null;
    closeModal();
  }
  else showNotification("Aucun asset sélectionné", "warning");
}

function createAsset () {
  showNotification("Cette fonctionnalité n'est pas encore développée", "error");
}
