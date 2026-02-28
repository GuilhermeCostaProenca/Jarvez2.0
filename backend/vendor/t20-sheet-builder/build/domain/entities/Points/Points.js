"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Points = void 0;
const FixedModifiersList_1 = require("../Modifier/FixedModifier/FixedModifiersList");
const PerLevelModifiersList_1 = require("../Modifier/PerLevelModifier/PerLevelModifiersList");
class Points {
    constructor(type) {
        this.type = type;
        this.fixedModifiers = new FixedModifiersList_1.FixedModifiersList();
        this.perLevelModifiers = new PerLevelModifiersList_1.PerLevelModifiersList();
    }
    addModifier(modifier) {
        this.fixedModifiers.add(modifier);
    }
    addPerLevelModifier(modifier) {
        this.perLevelModifiers.add(modifier);
    }
    getMax(calculator) {
        return calculator.calculate(this.fixedModifiers, this.perLevelModifiers);
    }
}
exports.Points = Points;
