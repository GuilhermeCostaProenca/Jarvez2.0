"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Equipment = void 0;
const EquipmentImprovementCategory_1 = require("./EquipmentImprovement/EquipmentImprovementCategory");
class Equipment {
    constructor() {
        this.improvements = [];
    }
    addImprovement(improvement) {
        if (improvement.category !== EquipmentImprovementCategory_1.EquipmentImprovementCategory.all
            && improvement.category !== this.categoryForImprovement) {
            throw new Error(`Improvement ${improvement.name} is not compatible with ${this.name}`);
        }
        if (this.improvements.length >= 4) {
            throw new Error(`Equipment ${this.name} already has 4 improvements`);
        }
        this.improvements.push(improvement);
    }
    getTotalPrice() {
        return this.price + this.improvements.reduce((total, improvement, index) => {
            const price = Equipment.improvementPrices[index];
            return total + price;
        }, 0);
    }
    serialize() {
        return {
            name: this.name,
        };
    }
    onEquip(modifiers) {
        console.log('onEquip', this.name);
    }
    onUnequip(modifiers) {
        console.log('onUnequip', this.name);
    }
}
exports.Equipment = Equipment;
Equipment.improvementPrices = [300, 3000, 9000, 18000];
