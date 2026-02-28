"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EquipmentAnimal = void 0;
const Equipment_1 = require("../Equipment");
class EquipmentAnimal extends Equipment_1.Equipment {
    get isWieldable() {
        return false;
    }
    constructor(name, price = 0) {
        super();
        this.name = name;
        this.price = price;
        this.categoryForImprovement = null;
    }
}
exports.EquipmentAnimal = EquipmentAnimal;
