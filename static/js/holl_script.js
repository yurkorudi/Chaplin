let hallStructure = [];
let hallId = null;

function createElement(tag, ...classNames) {
    const el = document.createElement(tag);
    el.classList.add(...classNames);
    return el;
}

function clearHoll() {
    const holl = document.getElementById("holl");
    holl.innerHTML = "";
}

function setHollStyle(holl, columns) {
    holl.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
}

function renderHall() {
    const holl = document.getElementById("holl");
    clearHoll();

    const rows = hallStructure.length;
    const columns = Math.max(...hallStructure.map(row => row.length));
    setHollStyle(holl, columns + 1);

    hallStructure.forEach((row, rowIndex) => {
        for (let col = 0; col < columns; col++) {
            const val = row[col] ?? 0;
            let seat;
            if (val === 0) {
                seat = createElement("div", "empty");
            } else if (val === 2) {
                seat = createElement("div", "seat", "vip");
            } else {
                seat = createElement("div", "seat");
            }

            seat.dataset.row = rowIndex;
            seat.dataset.col = col;
            seat.addEventListener("click", () => {
                if (hallStructure[rowIndex][col] === 1) hallStructure[rowIndex][col] = 2;
                else if (hallStructure[rowIndex][col] === 2) hallStructure[rowIndex][col] = 1;
                renderHall();
            });
            holl.appendChild(seat);
        }

        const addButton = createElement("button", "add");
        addButton.innerText = "+";
        addButton.dataset.row = rowIndex;
        addButton.addEventListener("click", () => {
            const row = hallStructure[rowIndex];
            let added = false;

            for (let i = 0; i < row.length; i++) {
                if (row[i] === 0) {
                    row[i] = 1;
                    added = true;
                    break;
                }
            }

            if (!added) {
                const newColIndex = Math.max(...hallStructure.map(r => r.length));
                hallStructure.forEach((r, i) => {
                    r[newColIndex] = (i === rowIndex) ? 1 : 0;
                });
            }
            renderHall();
        });
        holl.appendChild(addButton);
    });

    const vipRow = createElement("div");
    vipRow.style.gridColumn = `span ${columns + 1}`;
    vipRow.style.display = "contents";

    for (let j = 0; j < columns; j++) {
        const vipButton = createElement("button", "add");
        vipButton.innerText = "+";
        vipButton.dataset.columns = j;
        vipButton.addEventListener("click", () => {
            const newRow = Array(columns).fill(0);
            newRow[j] = 2;
            hallStructure.push(newRow);
            renderHall();
        });
        vipRow.appendChild(vipButton);
    }

    holl.appendChild(vipRow);
}

function main() {
    const rows = Number(document.getElementById("rows").value);
    const columns = Number(document.getElementById("columns").value);
    hallStructure = Array.from({ length: rows }, () => Array(columns).fill(1));
    renderHall();
}

document.querySelectorAll('.cinema-link').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const rows = Number(this.dataset.rows);
        const columns = Number(this.dataset.columns);
        hallId = this.dataset.id;

        document.getElementById("rows").value = rows;
        document.getElementById("columns").value = columns;

        if (this.dataset.structure) {
            hallStructure = JSON.parse(this.dataset.structure);
        } else {
            hallStructure = Array.from({ length: rows }, () => Array(columns).fill(1));
        }
        renderHall();
    });
});

function saveStructure() {
    if (!hallId) return alert("Виберіть кінотеатр спочатку.");
    fetch(`/api/save_hall_structure/${hallId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(hallStructure)
    }).then(res => {
        if (res.ok) alert("Збережено успішно!");
        else alert("Помилка при збереженні!");
    });
}