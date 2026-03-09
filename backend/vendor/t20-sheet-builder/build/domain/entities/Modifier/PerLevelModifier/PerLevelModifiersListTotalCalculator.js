"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerLevelModifiersListTotalCalculator = void 0;
const PerLevelModifierAppliableValueCalculator_1 = require("./PerLevelModifierAppliableValueCalculator");
class PerLevelModifiersListTotalCalculator {
    constructor(attributes, level) {
        this.attributes = attributes;
        this.level = level;
    }
    calculate(modifiers) {
        return modifiers.reduce((acc, modifier) => {
            const getter = new PerLevelModifierAppliableValueCalculator_1.PerLevelModifierAppliableValueCalculator(this.attributes, this.level, modifier);
            return modifier.getAppliableValue(getter) + acc;
        }, 0);
    }
}
exports.PerLevelModifiersListTotalCalculator = PerLevelModifiersListTotalCalculator;
