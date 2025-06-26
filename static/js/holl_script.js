let startColumns;
let extraRows = [];

function getData(inputID) {
    const input = document.getElementById(inputID);
    const value = Number(input.value);
    const valid = checkValid(input, value);
    if (valid) {
        return value;
    }
}

function checkValid(input, value) {
    if (!isNaN(value) && value !== " ") {
        return true;
    } else {
        input.value = "";
        return false;
    }
}

function setHollStyle(holl, columns) {
    const number = columns + 1;
    holl.style.display = 'grid';
    holl.style.gridTemplateColumns = `repeat(${number}, 1fr)`;
}

function createElement(element, ...className) {
    const created = document.createElement(element);
    created.classList.add(...className);
    return created;
}

function createFill(holl, rows, columns, empty = false) {
    const placeCount = rows * columns;
    let t = 1;
    let rowCount = 1;
    let extraSeats = 0;

    for (let i = 1; i <= placeCount; i++) {
        const k = (i - 1) % columns + 1;

        if (k === 1) {
            const count = extraRows.filter(n => n === rowCount).length;
            extraSeats = count - extraSeats;
        }

        let seat;
        if (!empty) {
            seat = createElement("div", "seat");
        } else {
            if (k <= startColumns) {
                seat = createElement("div", "seat");
            } else if (extraSeats > 0) {
                seat = createElement("div", "seat");
                extraSeats--;
            } else {
                seat = createElement("div", "empty");
            }
        }

        holl.appendChild(seat);

        if (t === columns || i === placeCount) {
            const addButton = createElement("button", "add");
            addButton.dataset.row = rowCount;
            addButton.textContent = "+";  // Для зручності
            addButton.addEventListener("click", function () {
                empty = true;
                const pressed = this.dataset.row;
                extraRows.push(Number(pressed));
                extraRows.sort((a, b) => a - b);

                const maxCount = Math.max(
                    ...extraRows.map(n => extraRows.filter(x => x === n).length)
                );

                const newCount = startColumns + maxCount;
                clearHoll();
                setHollStyle(holl, newCount);
                createHoll(newCount, true);
            });

            holl.appendChild(addButton);
            t = 0;
            rowCount++;
        }

        t++;
    }
}

function removeEl(className) {
    const elements = document.querySelectorAll(className);
    elements.forEach(el => el.remove());
}

function createHoll(extraColumns = 0, empty = false) {
    const holl = document.getElementById("holl");
    const rows = getData("rows");
    let columns = 0;

    if (extraColumns > 0) {
        columns = extraColumns;
    } else {
        columns = getData("columns");
        startColumns = columns;
    }

    createFill(holl, rows, columns, empty);
    setHollStyle(holl, columns);
}

function clearHoll() {
    removeEl(".seat");
    removeEl(".add");
    removeEl(".empty");
}

function main() {
    clearHoll();
    createHoll();
}
