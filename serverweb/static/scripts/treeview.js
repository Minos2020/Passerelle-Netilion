

let selectedElement = null;

function createTree(data) {
  
  const container = document.getElementById('treeview-container');
  container.innerHTML = ""; // reset
  const root = document.createElement('div');

  // Construire une map des assets et tags
  const assetsById = Object.fromEntries(data.assets.map(a => [a.id, a]));
  const tagsByAsset = {};
  data.instrumentations.forEach(tag => {
    tag.assets.forEach(assetId => {
      if (!tagsByAsset[assetId]) tagsByAsset[assetId] = [];
      tagsByAsset[assetId].push(tag);
    });
  });

  // Noeuds par parent
  const nodesByParent = {};
  data.nodes.forEach(node => {
    const pid = node.parent_id || 'root';
    if (!nodesByParent[pid]) nodesByParent[pid] = [];
    nodesByParent[pid].push(node);
  });

  // Assets par node
  const assetsByNode = {};
  data.assets.forEach(asset => {
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
    label.onclick = () => el.classList.toggle('open');
  
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
  
    // Tags rattachés directement à ce node sans asset
    data.instrumentations.forEach(tag => {
      if (tag.nodes.includes(node.id) && tag.assets.length === 0) {
        children.appendChild(buildTag(tag));
      }
    });
  
    el.appendChild(label);
    el.appendChild(children);
    return el;
  }
  

  function buildAsset(asset) {
    const hasTags = tagsByAsset[asset.id]?.length > 0;
    const el = document.createElement('div');
    el.className = `tree-node ${hasTags ? 'folder' : 'asset'}`;
  
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = asset.product_name + (asset.description ? ` (${asset.description})` : '');
  
    if (hasTags) {
      label.onclick = () => el.classList.toggle('open');
    } else {
      label.onclick = () => {
        if (selectedElement) selectedElement.classList.remove('selected');
        el.classList.add('selected');
        selectedElement = el;
        console.log('Selected asset:', asset);
      };
    }
  
    const children = document.createElement('div');
    children.className = 'children';
  
    (tagsByAsset[asset.id] || []).forEach(tag => {
      const tagEl = buildTag(tag);
      children.appendChild(tagEl);
    });
  
    el.appendChild(label);
    if (hasTags) el.appendChild(children);
    return el;
  }
  

  function buildTag(tag) {
    const el = document.createElement('div');
    el.className = 'tree-node file';

    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = tag.tag;

    label.onclick = () => {
      if (selectedElement) selectedElement.classList.remove('selected');
      el.classList.add('selected');
      selectedElement = el;

      console.log('Selected tag:', tag); // ici tu peux faire un callback
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


