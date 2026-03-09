"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextualModifiersList = void 0;
const ModifiersList_1 = require("../ModifiersList");
const ContextualModifierAppliableValueCalculator_1 = require("./ContextualModifierAppliableValueCalculator");
const ContextualModifiersListTotalCalculator_1 = require("./ContextualModifiersListTotalCalculator");
class ContextualModifiersList extends ModifiersList_1.ModifiersList {
    serialize(sheet, context) {
        const attributes = sheet.getSheetAttributes().getValues();
        const totalCalculator = new ContextualModifiersListTotalCalculator_1.ContextualModifiersListTotalCalculator(context, attributes);
        return {
            modifiers: this.modifiers.map(modifier => {
                const calculator = new ContextualModifierAppliableValueCalculator_1.ContextualModifierAppliableValueCalculator(attributes, context, modifier);
                return modifier.serialize(calculator, attributes);
            }),
            total: this.getTotal(totalCalculator),
            maxTotal: this.getMaxTotal(attributes),
        };
    }
    getMaxTotal(attributes) {
        return this.modifiers.reduce((acc, modifier) => modifier.baseValue + modifier.getTotalAttributeBonuses(attributes) + acc, 0);
    }
}
exports.ContextualModifiersList = ContextualModifiersList;
