let selectedElementUI = null;
let selectedElementObj = null;
let selectedParentUI = null;
let selectedParentObj = null;

let lastSelectedObjectType = null;

function createTree(account, bindingIndex) {
  
  const container = document.getElementById('treeview-container');
  container.innerHTML = ""; // reset
  const root = document.createElement('div');

  const selectButton = document.getElementById('select-button');
  const createButton = document.getElementById('open-create--asset-modal-button');

  selectButton.onclick = () => {
      selectObject(bindingIndex, account);
  };

  createButton.onclick = () => {
    openCreateAssetModal(bindingIndex, account, selectedParentObj);
  };

  document.getElementById("delete-asset-button").onclick = () => {
    // Afficher la fenêtre de confirmation

    // Si l'objet est un asset
    if (lastSelectedObjectType){
      document.getElementById("delete-confirmation-text").textContent = "Êtes-vous sûr de vouloir supprimer cet élément ? ("+lastSelectedObjectType+")";
      document.getElementById("confirmation-modal").style.display = "flex";
    } 
    else showNotification("Aucun élément sélectionné", "warning");
      
      
  }

  // Annuler la suppression
  document.getElementById("cancel-delete-object").onclick = () => {
    // Cacher la fenêtre de confirmation
    document.getElementById("confirmation-modal").style.display = "none";
  }

  // Confirmer la suppression
  document.getElementById("confirm-delete-object").onclick = async() => {
    
    let objectToDelete = null;
    if (lastSelectedObjectType == "asset"){
      objectToDelete = selectedElementObj;
    } else objectToDelete = selectedParentObj;

    try {
      let response = await fetch("/api/delete_object", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              account_id: account.account_id,
              object_id: objectToDelete.id,
              object_type: lastSelectedObjectType
            })
        });
        
        let data = await response.json();
        
        if (response.ok && data.success) {
          showNotification("Objet supprimé !", "success");
          
          // redemande les données afin de mettre à jour l'affichage
          createTree(data.account, bindingIndex)
          fetchData();
        } else if (response.ok && !data.success) {
          showNotification("Problème lors de la suppression de l'asset : " + data.error, "error", 6000);
        } else {
          showNotification("Erreur HTTP : " + response.status, "error", 6000);
        }        
    } catch (error) {
      showNotification(error, "error", 6000);
    }
    lastSelectedObjectType = null;
    
    // Cacher la fenêtre de confirmation
    document.getElementById("confirmation-modal").style.display = "none";
  }


  // Assets par tag en fonction des instrumentations associes à chaque asset
  let assetsByTag = {};
  account.assets.forEach(asset => {
    asset.instrumentations.forEach(tagId => {
      if (!assetsByTag[tagId]) assetsByTag[tagId] = [];
      assetsByTag[tagId].push(asset);
    });
  });

  // tags par Noeud
  let tagsByNode = {};
  let tagsWithoutNode = [];
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
  let nodesByParent = {};
  account.nodes.forEach(node => {
    const pid = node.parent_id || 'root';
    if (!nodesByParent[pid]) nodesByParent[pid] = [];
    nodesByParent[pid].push(node);
  });

  // Sous-assets par asset
  let subAssetsByAsset = {};
  account.assets.forEach(asset => {
    let pid = asset.parent_id || null;
    if(!subAssetsByAsset[pid]) subAssetsByAsset[pid] = [];
    if(pid) subAssetsByAsset[pid].push(asset);
  });

  // console.log("Sous-assets : ", subAssetsByAsset);

  // Assets par node
  let assetsByNode = {};
  let assetsWithoutNode = [];
  account.assets.forEach(asset => {
    if (asset.parent_id == null) { // ne prend pas en compte les sous-assets
      if (!asset.nodes.length > 0 && !asset.instrumentations.length > 0) assetsWithoutNode.push(asset);
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
        if (selectedParentUI) selectedParentUI.classList.remove('selected'); selectedParentUI = null;
      } 
      else if (selectedParentUI) selectedParentUI.classList.remove('selected');
      
      el.classList.add('selected');
      selectedParentUI = el;
      selectedParentObj = node;
      lastSelectedObjectType = "node";

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
      lastSelectedObjectType = "asset";
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
        if (selectedParentUI) selectedParentUI.classList.remove('selected'); selectedParentUI = null;
      } 
      else if (selectedParentUI) selectedParentUI.classList.remove('selected');
      
      el.classList.add('selected');
      selectedParentUI = el;
      selectedParentObj = tag;
      lastSelectedObjectType = "instrumentation";
      
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
    closeSelectAssetModal();
  }
  else showNotification("Aucun asset sélectionné", "warning");
}

function resetAllSelections() {
  selectedElementUI = null;
  selectedElementObj = null;
  selectedParentUI = null;
  selectedParentObj = null;
  lastSelectedObjectType = null;
}