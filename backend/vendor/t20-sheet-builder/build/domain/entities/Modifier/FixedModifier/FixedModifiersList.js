"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixedModifiersList = void 0;
const ModifiersList_1 = require("../ModifiersList");
const FixedModifierAppliableValueCalculator_1 = require("./FixedModifierAppliableValueCalculator");
const FixedModifiersListTotalCalculator_1 = require("./FixedModifiersListTotalCalculator");
class FixedModifiersList extends ModifiersList_1.ModifiersList {
    serialize(sheet, _context) {
        const attributes = sheet.getSheetAttributes().getValues();
        const appliableValueCalculator = new FixedModifierAppliableValueCalculator_1.FixedModifierAppliableValueCalculator(attributes);
        const modifiers = this.modifiers.map(modifier => modifier.serialize(appliableValueCalculator, attributes));
        const totalCalculator = new FixedModifiersListTotalCalculator_1.FixedModifiersListTotalCalculator(attributes);
        return {
            modifiers,
            total: this.getTotal(totalCalculator),
        };
    }
}
exports.FixedModifiersList = FixedModifiersList;
