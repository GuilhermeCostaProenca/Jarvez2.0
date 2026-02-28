"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerLevelModifierAppliableValueCalculator = void 0;
const ModifierValueGetter_1 = require("../ModifierValueGetter");
class PerLevelModifierAppliableValueCalculator extends ModifierValueGetter_1.ModifierAppliableValueCalculator {
    constructor(attributes, level, modifier) {
        super(attributes);
        this.level = level;
        this.modifier = modifier;
    }
    calculate(value, attributes) {
        const attributeBonuses = this.getAttributesBonusesTotal(attributes);
        const perLevelValue = value + attributeBonuses;
        if (!this.modifier.includeFirstLevel) {
            return Math.floor((this.level - 1) / this.modifier.frequency) * perLevelValue;
        }
        return Math.floor(this.level / this.modifier.frequency) * perLevelValue;
    }
}
exports.PerLevelModifierAppliableValueCalculator = PerLevelModifierAppliableValueCalculator;
