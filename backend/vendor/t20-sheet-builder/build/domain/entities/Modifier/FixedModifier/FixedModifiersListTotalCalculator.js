"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixedModifiersListTotalCalculator = void 0;
const FixedModifierAppliableValueCalculator_1 = require("./FixedModifierAppliableValueCalculator");
class FixedModifiersListTotalCalculator {
    constructor(attributes) {
        this.attributes = attributes;
    }
    calculate(modifiers) {
        const getter = new FixedModifierAppliableValueCalculator_1.FixedModifierAppliableValueCalculator(this.attributes);
        return modifiers.reduce((acc, modifier) => acc + modifier.getAppliableValue(getter), 0);
    }
}
exports.FixedModifiersListTotalCalculator = FixedModifiersListTotalCalculator;
