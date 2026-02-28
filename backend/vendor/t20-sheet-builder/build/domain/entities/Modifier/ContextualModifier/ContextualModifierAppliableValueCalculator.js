"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextualModifierAppliableValueCalculator = void 0;
const ModifierValueGetter_1 = require("../ModifierValueGetter");
class ContextualModifierAppliableValueCalculator extends ModifierValueGetter_1.ModifierAppliableValueCalculator {
    constructor(attributes, context, modifier) {
        super(attributes);
        this.context = context;
        this.modifier = modifier;
    }
    calculate(value, attributes) {
        const bonusesTotal = this.getAttributesBonusesTotal(attributes);
        if (this.context.activateContextualModifiers
            && this.modifier.condition.verify(this.context)) {
            return value + bonusesTotal;
        }
        return 0;
    }
}
exports.ContextualModifierAppliableValueCalculator = ContextualModifierAppliableValueCalculator;
