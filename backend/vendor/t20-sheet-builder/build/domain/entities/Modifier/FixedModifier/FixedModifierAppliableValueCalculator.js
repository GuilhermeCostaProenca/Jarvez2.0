"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixedModifierAppliableValueCalculator = void 0;
const ModifierValueGetter_1 = require("../ModifierValueGetter");
class FixedModifierAppliableValueCalculator extends ModifierValueGetter_1.ModifierAppliableValueCalculator {
    calculate(baseValue, attributeBonuses) {
        return baseValue + this.getAttributesBonusesTotal(attributeBonuses);
    }
}
exports.FixedModifierAppliableValueCalculator = FixedModifierAppliableValueCalculator;
