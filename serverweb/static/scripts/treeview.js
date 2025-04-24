let selectedElementUI = null;
let selectedElementObj = null;
let selectedParent = null;

function createTree(account, bindingIndex) {
  
  const container = document.getElementById('treeview-container');
  container.innerHTML = ""; // reset
  const root = document.createElement('div');

  const selectButton = document.getElementById('select-button');

  selectButton.onclick = () => {
      selectObject(bindingIndex, account);
  };

  // Assets par tag en fonction des instrumentations associes à chaque asset
  const assetsByTag = {};
  account.assets.forEach(asset => {
    asset.instrumentations.forEach(tagId => {
      if (!assetsByTag[tagId]) assetsByTag[tagId] = [];
      assetsByTag[tagId].push(asset);
    });
  });

  // tags par Noeud
  const tagsByNode = {};
  const tagsWithoutNode = [];
  account.instrumentations.forEach(tag => {
    if (!tag.nodes.length > 0) tagsWithoutNode.push(tag);
    else {
      tag.nodes.forEach(nodeId => {
        if (!tagsByNode[nodeId]) tagsByNode[nodeId] = [];
        tagsByNode[nodeId].push(tag);
      });
    }
  });

  // Noeuds par parent
  const nodesByParent = {};
  account.nodes.forEach(node => {
    const pid = node.parent_id || 'root';
    if (!nodesByParent[pid]) nodesByParent[pid] = [];
    nodesByParent[pid].push(node);
  });

  // Sous-assets par asset
  const subAssetsByAsset = {};
  account.assets.forEach(asset => {
    const pid = asset.parent_id || null;
    if(!subAssetsByAsset[pid]) subAssetsByAsset[pid] = [];
    if(pid) subAssetsByAsset[pid].push(asset);
  });

  // console.log("Sous-assets : ", subAssetsByAsset);

  // Assets par node
  const assetsByNode = {};
  const assetsWithoutNode = [];
  account.assets.forEach(asset => {
    if (asset.parent_id == null) { // filtre les assets sans parent
      if (!asset.nodes.length > 0) assetsWithoutNode.push(asset);
      else {
        asset.nodes.forEach(nodeId => {
          if (!assetsByNode[nodeId]) assetsByNode[nodeId] = [];
          assetsByNode[nodeId].push(asset);
        });
      }
    }
  });


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
      }
        // console.log('Selected folder :', node);
      el.classList.toggle('open');
      // console.log(el.classList);
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
  
    el.appendChild(label);
    el.appendChild(children);
    return el;
  }
  

  function buildAsset(asset) {
    const el = document.createElement('div');
    el.className = `tree-node asset`;
  
    // Header permettant de placer correctement le symbole à gauche
    const header = document.createElement('div');
    header.className = 'header';
  
    header.onclick = () => {
      if (selectedElementUI) selectedElementUI.classList.remove('selected');
      el.classList.add('selected');
      selectedElementUI = el;
      selectedElementObj = asset;
      el.classList.toggle('open');
      // console.log(el.classList);
    };
  
    // Label contenant les élément de l'asset
    const label = document.createElement('div');
    label.className = 'label';
    label.style.fontSize = '1em';
    label.innerHTML = `
      <div>
        ${asset.serial_number ? '<b>' + asset.serial_number + '</b>' : ""} - ${asset.product_name}
      </div>
      <div>
        <i>${asset.description ? '(' + asset.description + ')' : ""}</i>
      </div>
    `;
  
    header.appendChild(label);
  
    const children = document.createElement('div');
    children.className = 'children';
  
    // Sous-assets
    (subAssetsByAsset[asset.id] || []).forEach(subAsset => {
      children.appendChild(buildAsset(subAsset));
    });
  
    el.appendChild(header);
    el.appendChild(children);
  
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
      // console.log(el.classList);
      // console.log('Selected object (tag) :', tag); // ici tu peux faire un callback
    };

    const children = document.createElement('div');
    children.className = 'children';

    // Assets dans ce tag
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

function selectObject (bindingIndex, account) {
  if (selectedElementUI && selectedElementObj){
    bindings[bindingIndex].netilion_binding_id = selectedElementObj.id;
    
    if (account.assets.includes(selectedElementObj)) {
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
    closeSelectAssetModal();
  }
  else showNotification("Aucun asset sélectionné", "warning");
}
