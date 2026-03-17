"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Defense = void 0;
const FixedModifiersList_1 = require("../Modifier/FixedModifier/FixedModifiersList");
class Defense {
    constructor() {
        this.attribute = 'dexterity';
        this.fixedModifiers = new FixedModifiersList_1.FixedModifiersList();
    }
    addFixedModifier(modifier) {
        this.fixedModifiers.add(modifier);
    }
    getTotal(calculator) {
        return calculator.calculate(this.attribute, this.fixedModifiers);
    }
}
exports.Defense = Defense;
