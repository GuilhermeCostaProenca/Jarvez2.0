"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextualModifiersListTotalCalculator = void 0;
const ContextualModifierAppliableValueCalculator_1 = require("./ContextualModifierAppliableValueCalculator");
class ContextualModifiersListTotalCalculator {
    constructor(context, attributes) {
        this.context = context;
        this.attributes = attributes;
    }
    calculate(modifiers) {
        return modifiers.reduce((acc, modifier) => {
            const getter = new ContextualModifierAppliableValueCalculator_1.ContextualModifierAppliableValueCalculator(this.attributes, this.context, modifier);
            return modifier.getAppliableValue(getter) + acc;
        }, 0);
    }
}
exports.ContextualModifiersListTotalCalculator = ContextualModifiersListTotalCalculator;
