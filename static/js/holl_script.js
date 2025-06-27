        let startColumns;
        let extraRows = [];
        let extraColumns = new Set();

        function getData(inputID){
            const input = document.getElementById(inputID);
            const value = Number(input.value);
            
            valid = checkValid(input, value);
            
            if (valid){
                return value;
            }
        }

        function checkValid(input, value){
            if (!isNaN(value) && value != " "){
                return true;
            }
            else{
                input.value = "";
                return false;
            }
        }

        function setHollStyle(holl, columns){
            const number = columns + 1;
            holl.style.gridTemplateColumns = `repeat(${number}, 1fr)`;
        }

        function createElement(element, ...className){
            const created = document.createElement(element);
            created.classList.add(...className);
            return created;
        }

        function createFill(holl, rows, columns, empty = false){
            placeCount = 0;
            t = 1;
            rowCount = 1;
            extraSeats = 0;
            buttonCount = columns;


            if(extraColumns.size === 0){
                placeCount = rows * columns;
            }
            else{
                placeCount = (rows + 1) * columns;
            }

            for (let i = 1; i <= placeCount; i++){
                k = Number((i - 1) % columns + 1);
                
                if (k == 1){
                    count = extraRows.filter(n => n === rowCount).length;
                    extraSeats = count - extraSeats;
                }
                
                if(!empty){
                    seat = createElement("div", "seat");
                }
                else{
                    if(k <= startColumns && rowCount <= rows){
                        seat = createElement("div", "seat");
                        console.log(`1 ${extraColumns.has(k)}, ${rowCount > rows}, k = ${k}, rowCount = ${rowCount}, rows = ${rows}`);
                    }
                    else if(extraColumns.has(k) && rowCount > rows){
                        seat = createElement("div", "seat");
                        console.log(`2 ${extraColumns.has(k)}, ${rowCount > rows}, k = ${k}, rowCount = ${rowCount}, rows = ${rows}`);
                    }
                    else if(extraSeats > 0 && rowCount <= rows){
                        seat = createElement("div", "seat");
                        extraSeats--;
                        console.log(`3 ${extraColumns.has(k)}, ${rowCount > rows}, k = ${k}, rowCount = ${rowCount}, rows = ${rows}`);
                    }                    
                    else{                      
                        seat = createElement("div", "empty");
                        console.log(`4 ${extraColumns.has(k)}, ${rowCount > rows}, k = ${k}, rowCount = ${rowCount}, rows = ${rows}`);
                    }
                }

                
                
                // const seatDetails = {seatPlace: 1 }
                holl.appendChild(seat);
         
                if (t == columns || i == placeCount){
                    const addButton = createElement("button", "add"); 
                    addButton.dataset.row = rowCount;
                    addButton.addEventListener("click", function () {
                        empty = true;
                        const pressed = this.dataset.row;

                        extraRows.push(Number(pressed));
                        extraRows.sort((a, b) => a - b);
                        maxCount = Math.max(
                            ...extraRows.map(n => extraRows.filter(x => x === n).length)
                        );

                        newCount = startColumns + maxCount;
                        
                        clearHoll();
                        setHollStyle(holl, newCount);
                        createHoll(newCount, empty);
                    });
                    holl.appendChild(addButton);
                    t = 0;
                    // k = 0;
                    rowCount++;
                }
                
                t++;
            }

            for(let j = 0; j < buttonCount; j++){
                const addButton = createElement("button", "add"); 
                addButton.dataset.columns = j + 1;
                addButton.addEventListener("click", function () {
                empty = true;
                const pressed = this.dataset.columns;

                extraColumns.add(Number(pressed));
                console.log(extraColumns);
                        
                clearHoll();
                setHollStyle(holl, columns);
                createHoll(columns, empty);
                });
                holl.appendChild(addButton);
            }
        }

        function removeEl(className){
            const element = document.querySelectorAll(className);   
            element.forEach(el =>
                el.remove()
            );
        }

        function createHoll(extraColumns=0, empty=false){
            const holl = document.getElementById("holl");
            const rows = getData("rows");            
            let columns = 0;

            if(extraColumns > 0){
                columns = extraColumns;
            }
            else{
                columns = getData("columns");
                startColumns = columns;
            }

            createFill(holl, rows, columns, empty);
            setHollStyle(holl, columns);
            // setSeatStyle("seat");
        }

        function clearHoll(){
            removeEl(".seat");
            removeEl(".add");
            removeEl(".empty");
        }

        function main(){
            clearHoll();
            createHoll();
        }
        