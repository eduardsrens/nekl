const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const clearBtn = document.getElementById("clearBtn");
const randomBtn = document.getElementById("randomBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

const COLS = 40;
const ROWS = 25;
let grid = makeGrid(false);
let running = false;
let timer = null;
let drawing = false;
let drawValue = 1;

function makeGrid(value) {
  return Array.from({ length: ROWS }, () =>
    Array.from({ length: COLS }, () => typeof value === "function" ? value() : value)
  );
}

function resizeCanvas() {
  const rect = canvas.getBoundingRect?.();
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function draw() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const cellW = width / COLS;
  const cellH = height / ROWS;

  ctx.fillStyle = "#181b21";
  ctx.fillRect(0, 0, width, height);

  ctx.fillStyle = "#55d68b";
  for (let y = 0; y < ROWS; y++) {
    for (let x = 0; x < COLS; x++) {
      if (grid[y][x]) {
        ctx.fillRect(x * cellW + 1, y * cellH + 1, cellW - 2, cellH - 2);
      }
    }
  }

  ctx.strokeStyle = "#292d35";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = 0; x <= COLS; x++) {
    ctx.moveTo(x * cellW, 0);
    ctx.lineTo(x * cellW, height);
  }
  for (let y = 0; y <= ROWS; y++) {
    ctx.moveTo(0, y * cellH);
    ctx.lineTo(width, y * cellH);
  }
  ctx.stroke();
}

function countNeighbors(x, y) {
  let count = 0;
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      if (dx === 0 && dy === 0) continue;
      const nx = x + dx;
      const ny = y + dy;
      if (nx >= 0 && nx < COLS && ny >= 0 && ny < ROWS) count += grid[ny][nx];
    }
  }
  return count;
}

function step() {
  grid = grid.map((row, y) => row.map((alive, x) => {
    const neighbors = countNeighbors(x, y);
    return alive ? (neighbors === 2 || neighbors === 3 ? 1 : 0)
                 : (neighbors === 3 ? 1 : 0);
  }));
  draw();
}

function setRunning(value) {
  window.clearInterval(timer);
  timer = null;
  running = value;
  statusDot.classList.toggle("running", running);
  statusText.textContent = running ? "Darbojas" : "Apturēts";
  startBtn.disabled = running;

  if (running) {
    timer = window.setInterval(step, 110);
  }
}

function getCell(event) {
  const rect = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - rect.left) * COLS / rect.width);
  const y = Math.floor((event.clientY - rect.top) * ROWS / rect.height);
  return { x, y };
}

function paint(event) {
  const { x, y } = getCell(event);
  if (x >= 0 && x < COLS && y >= 0 && y < ROWS) {
    grid[y][x] = drawValue;
    draw();
  }
}

canvas.addEventListener("mousedown", (event) => {
  event.preventDefault();
  if (running) setRunning(false);
  drawing = true;
  drawValue = event.button === 2 ? 0 : 1;
  paint(event);
});

canvas.addEventListener("mousemove", (event) => {
  if (drawing) paint(event);
});

window.addEventListener("mouseup", () => { drawing = false; });
canvas.addEventListener("contextmenu", (event) => event.preventDefault());

startBtn.addEventListener("click", () => setRunning(true));
stopBtn.addEventListener("click", () => setRunning(false));
clearBtn.addEventListener("click", () => {
  setRunning(false);
  grid = makeGrid(false);
  draw();
});
randomBtn.addEventListener("click", () => {
  setRunning(false);
  grid = makeGrid(() => Math.random() < 0.28 ? 1 : 0);
  draw();
});

window.addEventListener("resize", resizeCanvas);
resizeCanvas();
