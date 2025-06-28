let selectedCinemaId = null;
let selectedHallId   = null;
let hallStructure    = [];

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-generate')
          .addEventListener('click', main);
  document.getElementById('btn-save')
          .addEventListener('click', saveStructure);
  document.querySelector('.holls')
          .addEventListener('click', onCinemaListClick);
});

function onCinemaListClick(e) {
  if (e.target.matches('.hall-link')) {
    e.preventDefault();
    selectedCinemaId = +e.target.dataset.cinemaId;
    selectedHallId   = +e.target.dataset.hallId;

    document.getElementById("rows").value    = +e.target.dataset.rows;
    document.getElementById("columns").value = +e.target.dataset.columns;
    hallStructure = JSON.parse(e.target.dataset.structure);
    renderHall();
    return;
  }
  if (e.target.matches('.new-hall-btn')) {
    selectedCinemaId = +e.target.dataset.cinemaId;
    selectedHallId   = null;

    document.getElementById("rows").value    = '';
    document.getElementById("columns").value = '';
    hallStructure = [];
    clearHoll();
    alert(`Вибрано кінотеатр ID=${selectedCinemaId}.\n` +
          `Введіть rows і columns та натисніть Submit.`);
  }
}

function createElement(tag, ...classNames) {
  const el = document.createElement(tag);
  classNames
    .filter(c => c && c.trim())
    .forEach(c => el.classList.add(c));
  return el;
}

function clearHoll() {
  document.getElementById("holl").innerHTML = "";
}

function setHollStyle(holl, cols) {
  holl.style.display = "grid";
  holl.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  holl.style.gap = "8px";
}

function renderHall() {
  const holl = document.getElementById("holl");
  clearHoll();

  const rows    = hallStructure.length;
  const columns = rows ? hallStructure[0].length : 0;
  setHollStyle(holl, columns + 1);


  hallStructure.forEach((row, i) => {
    row.forEach((val, j) => {
      const seat = val === 0
        ? createElement("div", "empty")
        : createElement("div", "seat", val === 2 ? "vip" : "");
      seat.addEventListener("click", () => {
        hallStructure[i][j] = hallStructure[i][j] === 1 ? 2 : 1;
        renderHall();
      });
      holl.appendChild(seat);
    });
    const btnRow = createElement("button", "add");
    btnRow.innerText = "+";
    btnRow.addEventListener("click", () => {
      let added = false;
      for (let k = 0; k < row.length; k++) {
        if (row[k] === 0) { row[k] = 1; added = true; break; }
      }
      if (!added) {
        hallStructure.forEach((r, idx) => r.push(idx === i ? 1 : 0));
      }
      renderHall();
    });
    holl.appendChild(btnRow);
  });


  for (let j = 0; j < columns; j++) {
    const vipBtn = createElement("button", "add", "vip-btn");
    vipBtn.innerText = "+";
    vipBtn.style.gridColumnStart = j + 1;
    vipBtn.style.gridRowStart    = rows + 1;
    vipBtn.addEventListener("click", () => {
      const vipIdx = hallStructure.findIndex(r =>
        r.includes(2) && r.every(v => v===0||v===2)
      );
      if (vipIdx >= 0) hallStructure[vipIdx][j] = 2;
      else {
        const newRow = Array(columns).fill(0);
        newRow[j] = 2;
        hallStructure.push(newRow);
      }
      renderHall();
    });
    holl.appendChild(vipBtn);
  }
}

function main() {
  const rows = Number(document.getElementById("rows").value);
  const cols = Number(document.getElementById("columns").value);
  if (!rows || !cols) return alert("Вкажіть обидва числа!");
  hallStructure = Array.from({length: rows}, () => Array(cols).fill(1));
  renderHall();
}

function saveStructure() {
  if (!selectedCinemaId && !selectedHallId) {
    return alert("Спочатку виберіть зал або натисніть «Додати новий зал».");
  }

  let url, method, body;
  if (selectedHallId) {
    url    = `/api/halls/${selectedHallId}`;
    method = 'PUT';
    body   = { structure: hallStructure };
  } else {
    url    = '/api/halls';
    method = 'POST';
    body   = {
      cinema_id: selectedCinemaId,
      rows:      hallStructure.length,
      columns:   hallStructure[0].length,
      structure: hallStructure
    };
  }

  fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  })
  .then(r => r.ok ? r.json() : Promise.reject(r))
  .then(() => {
    alert("Успішно збережено!");
    location.reload();
  })
  .catch(() => alert("Помилка збереження — перевір логи сервера."));
}
