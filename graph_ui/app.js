const canvas = document.getElementById("graph");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const searchInput = document.getElementById("search");
const toggles = Array.from(document.querySelectorAll(".toggle input"));

const colors = {
  user: "#4ed4ff",
  server: "#f3b562",
  highlight: "#f472b6",
  membership: "#4ed4ff",
  mutual_friend: "#7b5cff",
  mutual_server: "#f3b562",
};

let graph = { nodes: [], edges: [] };
let nodes = [];
let edges = [];
let selectedNode = null;
let hoveredNode = null;
let scale = 1;
let offsetX = 0;
let offsetY = 0;
let isPanning = false;
let lastPan = { x: 0, y: 0 };

const settings = {
  repulsion: 2800,
  springLength: 120,
  springStrength: 0.008,
  damping: 0.85,
  maxVelocity: 6,
};

function resize() {
  canvas.width = canvas.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.clientHeight * window.devicePixelRatio;
  ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
}

window.addEventListener("resize", resize);

function randomPosition(radius = 200) {
  const angle = Math.random() * Math.PI * 2;
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  };
}

function buildSimulation(data) {
  nodes = data.nodes.map((node) => {
    const { x, y } = randomPosition(300 + Math.random() * 100);
    return {
      ...node,
      x,
      y,
      vx: 0,
      vy: 0,
    };
  });

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  edges = data.edges
    .map((edge) => ({
      ...edge,
      sourceNode: nodeMap.get(edge.source),
      targetNode: nodeMap.get(edge.target),
    }))
    .filter((edge) => edge.sourceNode && edge.targetNode);
}

function applyForces() {
  for (let i = 0; i < nodes.length; i += 1) {
    const nodeA = nodes[i];
    for (let j = i + 1; j < nodes.length; j += 1) {
      const nodeB = nodes[j];
      const dx = nodeA.x - nodeB.x;
      const dy = nodeA.y - nodeB.y;
      const distanceSq = dx * dx + dy * dy + 0.01;
      const force = settings.repulsion / distanceSq;
      const fx = (dx / Math.sqrt(distanceSq)) * force;
      const fy = (dy / Math.sqrt(distanceSq)) * force;
      nodeA.vx += fx;
      nodeA.vy += fy;
      nodeB.vx -= fx;
      nodeB.vy -= fy;
    }
  }

  edges.forEach((edge) => {
    if (!isEdgeVisible(edge.type)) {
      return;
    }
    const { sourceNode, targetNode } = edge;
    const dx = targetNode.x - sourceNode.x;
    const dy = targetNode.y - sourceNode.y;
    const distance = Math.sqrt(dx * dx + dy * dy) || 1;
    const displacement = distance - settings.springLength;
    const force = displacement * settings.springStrength;
    const fx = (dx / distance) * force;
    const fy = (dy / distance) * force;
    sourceNode.vx += fx;
    sourceNode.vy += fy;
    targetNode.vx -= fx;
    targetNode.vy -= fy;
  });

  nodes.forEach((node) => {
    node.vx *= settings.damping;
    node.vy *= settings.damping;
    node.vx = Math.max(-settings.maxVelocity, Math.min(settings.maxVelocity, node.vx));
    node.vy = Math.max(-settings.maxVelocity, Math.min(settings.maxVelocity, node.vy));
    node.x += node.vx;
    node.y += node.vy;
  });
}

function isEdgeVisible(edgeType) {
  const toggle = toggles.find((t) => t.dataset.edge === edgeType);
  return toggle ? toggle.checked : true;
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(offsetX, offsetY);
  ctx.scale(scale, scale);

  edges.forEach((edge) => {
    if (!isEdgeVisible(edge.type)) {
      return;
    }
    ctx.beginPath();
    ctx.strokeStyle = colors[edge.type] || "#2d3748";
    ctx.globalAlpha = edge.type === "membership" ? 0.4 : 0.6;
    ctx.lineWidth = 1.1;
    ctx.moveTo(edge.sourceNode.x, edge.sourceNode.y);
    ctx.lineTo(edge.targetNode.x, edge.targetNode.y);
    ctx.stroke();
  });

  ctx.globalAlpha = 1;

  nodes.forEach((node) => {
    ctx.beginPath();
    const isSelected = selectedNode && selectedNode.id === node.id;
    const isHovered = hoveredNode && hoveredNode.id === node.id;
    const color = isSelected || isHovered ? colors.highlight : colors[node.type] || colors.user;
    const radius = isSelected || isHovered ? node.size + 3 : node.size;
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = isSelected || isHovered ? 12 : 6;
    ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    if (isSelected || isHovered) {
      ctx.fillStyle = "#e6edf3";
      ctx.font = "12px 'Space Grotesk', sans-serif";
      ctx.fillText(node.label, node.x + radius + 6, node.y - radius - 2);
    }
  });

  ctx.restore();
}

function frame() {
  applyForces();
  draw();
  requestAnimationFrame(frame);
}

function toGraphCoords(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  const x = (clientX - rect.left - offsetX) / scale;
  const y = (clientY - rect.top - offsetY) / scale;
  return { x, y };
}

function findNodeAt(x, y) {
  for (let i = nodes.length - 1; i >= 0; i -= 1) {
    const node = nodes[i];
    const dx = node.x - x;
    const dy = node.y - y;
    if (Math.sqrt(dx * dx + dy * dy) <= node.size + 4) {
      return node;
    }
  }
  return null;
}

canvas.addEventListener("mousedown", (event) => {
  isPanning = true;
  lastPan = { x: event.clientX, y: event.clientY };
});

canvas.addEventListener("mousemove", (event) => {
  const coords = toGraphCoords(event.clientX, event.clientY);
  hoveredNode = findNodeAt(coords.x, coords.y);

  if (!isPanning) {
    return;
  }
  const dx = event.clientX - lastPan.x;
  const dy = event.clientY - lastPan.y;
  offsetX += dx;
  offsetY += dy;
  lastPan = { x: event.clientX, y: event.clientY };
});

canvas.addEventListener("mouseup", (event) => {
  isPanning = false;
  const coords = toGraphCoords(event.clientX, event.clientY);
  selectedNode = findNodeAt(coords.x, coords.y);
});

canvas.addEventListener("mouseleave", () => {
  isPanning = false;
  hoveredNode = null;
});

canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  const delta = Math.sign(event.deltaY) * -0.08;
  const newScale = Math.min(2.5, Math.max(0.3, scale + delta));
  scale = newScale;
});

searchInput.addEventListener("input", (event) => {
  const query = event.target.value.trim().toLowerCase();
  if (!query) {
    selectedNode = null;
    return;
  }
  selectedNode = nodes.find((node) => node.label.toLowerCase().includes(query)) || null;
});

function updateStatus(text) {
  statusEl.textContent = text;
}

function initGraph(data) {
  graph = data;
  buildSimulation(graph);
  resize();
  updateStatus(`${graph.nodes.length} nodes, ${graph.edges.length} edges`);
  frame();
}

async function loadGraph() {
  updateStatus("Loading graph data...");
  if (window.pywebview && window.pywebview.api) {
    return await window.pywebview.api.get_graph();
  }
  throw new Error("pywebview API not available. Run via graph_view.py");
}

function handleError(error) {
  updateStatus(error.message || "Failed to load graph");
}

window.addEventListener("pywebviewready", () => {
  loadGraph().then(initGraph).catch(handleError);
});

// Support running directly in a browser without pywebview
if (!window.pywebview) {
  updateStatus("Open with graph_view.py to load data");
}
