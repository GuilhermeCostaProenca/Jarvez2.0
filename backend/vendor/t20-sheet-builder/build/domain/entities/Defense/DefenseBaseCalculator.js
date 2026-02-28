"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefenseBaseCalculator = void 0;
class DefenseBaseCalculator {
    static get initialValue() {
        return 10;
    }
    constructor(attributes, armorBonus, shieldBonus) {
        this.attributes = attributes;
        this.armorBonus = armorBonus;
        this.shieldBonus = shieldBonus;
    }
    calculate(attribute) {
        return DefenseBaseCalculator.initialValue
            + this.attributes[attribute] + this.armorBonus + this.shieldBonus;
    }
}
exports.DefenseBaseCalculator = DefenseBaseCalculator;
