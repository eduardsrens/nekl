
    const maze = [
      "#########################",
      "#A  #       #           #",
      "# # # ##### # ######### #",
      "# #   #   #   #       # #",
      "# ##### # ##### ##### # #",
      "#     # #     #     #   #",
      "##### # ##### ##### ### #",
      "#   # #     #     #   # #",
      "# # # ##### ##### # # # #",
      "# #       #     #   #   #",
      "# ####### ##### ####### #",
      "#       #     #       # #",
      "# ##### ##### # ##### # #",
      "#     #       #     #  B#",
      "#########################"
    ];
    const cellSize = 26;
    const colors = ["#ff5364", "#43b5ff", "#44d39a", "#c27bff"];
    const moves = {
      up: [-1, 0],
      right: [0, 1],
      down: [1, 0],
      left: [0, -1]
    };
    const canvas = document.getElementById("maze");
    const ctx = canvas.getContext("2d");
    const start = findCell("A");
    const goal = findCell("B");
    const paths = findAllPaths();
    let player = { ...start };
    let direction = "right";
    let score = 0;
    let steps = 0;
    let hintIndex = -1;
    let hintVisible = false;
    let won = false;
    let timer = null;
    let autoStep = 0;
    let autoStarted = false;
    let dots = new Set();

    function findCell(marker) {
      for (let row = 0; row < maze.length; row++) {
        const col = maze[row].indexOf(marker);
        if (col !== -1) return { row, col };
      }
      throw new Error(`Labirintā nav atrasta šūna ${marker}`);
    }

    function findAllPaths() {
      const found = [];
      const visited = new Set([key(start)]);
      const path = [{ ...start }];

      function search(cell) {
        if (cell.row === goal.row && cell.col === goal.col) {
          found.push(path.map(point => ({ ...point })));
          return;
        }
        for (const [name, [dr, dc]] of Object.entries(moves)) {
          const next = { row: cell.row + dr, col: cell.col + dc };
          const id = key(next);
          if (
            maze[next.row]?.[next.col] &&
            maze[next.row][next.col] !== "#" &&
            !visited.has(id)
          ) {
            visited.add(id);
            path.push(next);
            search(next);
            path.pop();
            visited.delete(id);
          }
        }
      }

      search(start);
      return found;
    }

    function key(point) {
      return `${point.row},${point.col}`;
    }

    function resetDots() {
      dots = new Set();
      maze.forEach((line, row) => {
        [...line].forEach((cell, col) => {
          if (cell === " " && !(row === start.row && col === start.col)) {
            dots.add(key({ row, col }));
          }
        });
      });
      dots.delete(key(goal));
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      maze.forEach((line, row) => {
        [...line].forEach((tile, col) => {
          const x = col * cellSize;
          const y = row * cellSize;
          if (tile === "#") {
            ctx.fillStyle = "#26395d";
            ctx.fillRect(x, y, cellSize, cellSize);
            ctx.strokeStyle = "#344a72";
            ctx.lineWidth = 1;
            ctx.strokeRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
          } else {
            ctx.fillStyle = "#111a2d";
            ctx.fillRect(x, y, cellSize, cellSize);
            ctx.strokeStyle = "#1b2942";
            ctx.strokeRect(x, y, cellSize, cellSize);
            if (dots.has(key({ row, col }))) {
              ctx.beginPath();
              ctx.fillStyle = "#dbeafe";
              ctx.arc(x + cellSize / 2, y + cellSize / 2, 2.2, 0, Math.PI * 2);
              ctx.fill();
            }
          }
        });
      });

      if (hintVisible && paths[hintIndex]) {
        const route = paths[hintIndex];
        ctx.beginPath();
        route.forEach((point, index) => {
          const x = point.col * cellSize + cellSize / 2;
          const y = point.row * cellSize + cellSize / 2;
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = colors[hintIndex] + "a8";
        ctx.lineWidth = 8;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.stroke();
      }

      drawMarker(start, "A", "#53df9a");
      drawMarker(goal, "B", "#ff7180");
      drawPlayer();
    }

    function drawMarker(point, label, color) {
      const x = point.col * cellSize + cellSize / 2;
      const y = point.row * cellSize + cellSize / 2;
      ctx.beginPath();
      ctx.fillStyle = color;
      ctx.arc(x, y, 9, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#111827";
      ctx.font = "bold 11px Segoe UI, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(label, x, y + 0.5);
    }

    function drawPlayer() {
      const x = player.col * cellSize + cellSize / 2;
      const y = player.row * cellSize + cellSize / 2;
      const angles = { right: 0, down: Math.PI / 2, left: Math.PI, up: -Math.PI / 2 };
      const angle = angles[direction];
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.arc(x, y, 10, angle + 0.38, angle + Math.PI * 2 - 0.38);
      ctx.closePath();
      ctx.fillStyle = "#ffd43b";
      ctx.fill();
      ctx.beginPath();
      ctx.fillStyle = "#172033";
      ctx.arc(x + Math.cos(angle - 0.65) * 4, y + Math.sin(angle - 0.65) * 4, 1.4, 0, Math.PI * 2);
      ctx.fill();
    }

    function move(name) {
      if (won || timer) return;
      autoStarted = false;
      const [dr, dc] = moves[name];
      const next = { row: player.row + dr, col: player.col + dc };
      if (!maze[next.row]?.[next.col] || maze[next.row][next.col] === "#") return;
      direction = name;
      player = next;
      steps++;
      const id = key(player);
      if (dots.delete(id)) score += 10;
      updateStats();
      if (player.row === goal.row && player.col === goal.col) finishGame();
      draw();
    }

    function updateStats() {
      document.getElementById("score").textContent = score;
      document.getElementById("steps").textContent = steps;
      document.getElementById("pellets").textContent = dots.size;
    }

    function finishGame() {
      won = true;
      stopAuto();
      document.getElementById("message").textContent = "🎉 Mērķis sasniegts!";
    }

    function resetGame() {
      stopAuto();
      player = { ...start };
      direction = "right";
      score = 0;
      steps = 0;
      autoStep = 0;
      autoStarted = false;
      won = false;
      resetDots();
      document.getElementById("message").textContent = "Dodieties no A līdz B!";
      updateStats();
      draw();
    }

    function chooseHint(index) {
      stopAuto();
      autoStarted = false;
      hintIndex = index;
      hintVisible = true;
      document.getElementById("message").textContent =
        `Padoms: ceļš ${index + 1} — ${paths[index].length - 1} soļi`;
      document.querySelectorAll(".route-chip").forEach((button, i) => {
        button.classList.toggle("active", i === index);
      });
      draw();
    }

    function stopAuto() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      document.getElementById("auto").textContent = "▶ Izspēlēt ceļu";
    }

    function playHint() {
      if (timer) return;
      if (hintIndex < 0) chooseHint(0);
      if (!autoStarted) {
        resetGame();
        autoStarted = true;
      }
      const route = paths[hintIndex];
      document.getElementById("auto").textContent = "▶ Atsākt";
      timer = setInterval(() => {
        if (autoStep >= route.length - 1) {
          stopAuto();
          return;
        }
        const next = route[++autoStep];
        const dr = next.row - player.row;
        const dc = next.col - player.col;
        direction = Object.keys(moves).find(name =>
          moves[name][0] === dr && moves[name][1] === dc
        );
        player = { ...next };
        steps++;
        if (dots.delete(key(player))) score += 10;
        updateStats();
        if (player.row === goal.row && player.col === goal.col) finishGame();
        draw();
      }, 110);
    }

    document.addEventListener("keydown", event => {
      const controls = {
        ArrowUp: "up", w: "up", W: "up",
        ArrowRight: "right", d: "right", D: "right",
        ArrowDown: "down", s: "down", S: "down",
        ArrowLeft: "left", a: "left", A: "left"
      };
      const directionName = controls[event.key];
      if (directionName) {
        event.preventDefault();
        move(directionName);
      }
    });

    document.querySelectorAll(".dpad button").forEach(button => {
      button.addEventListener("click", () => move(button.dataset.dir));
    });
    document.getElementById("reset").addEventListener("click", resetGame);
    document.getElementById("hint").addEventListener("click", () => {
      const next = (hintIndex + 1) % paths.length;
      chooseHint(next);
    });
    document.getElementById("auto").addEventListener("click", playHint);
    document.getElementById("pause").addEventListener("click", stopAuto);

    document.getElementById("route-count").textContent =
      `${paths.length} iespējamie ceļi`;
    paths.forEach((path, index) => {
      const button = document.createElement("button");
      button.className = "route-chip";
      button.style.setProperty("--route-color", colors[index]);
      button.textContent = `Ceļš ${index + 1} · ${path.length - 1} soļi`;
      button.addEventListener("click", () => chooseHint(index));
      document.getElementById("routes").append(button);
    });

    resetDots();
    updateStats();
    draw();
  