"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerLevelModifiersList = void 0;
const Level_1 = require("../../Sheet/Level");
const ModifiersList_1 = require("../ModifiersList");
const PerLevelModifierAppliableValueCalculator_1 = require("./PerLevelModifierAppliableValueCalculator");
const PerLevelModifiersListTotalCalculator_1 = require("./PerLevelModifiersListTotalCalculator");
class PerLevelModifiersList extends ModifiersList_1.ModifiersList {
    serialize(sheet, context) {
        const attributes = sheet.getSheetAttributes().getValues();
        const level = sheet.getLevel();
        const totalCalculator = new PerLevelModifiersListTotalCalculator_1.PerLevelModifiersListTotalCalculator(attributes, level);
        return {
            modifiers: this.modifiers.map(modifier => {
                const calculator = new PerLevelModifierAppliableValueCalculator_1.PerLevelModifierAppliableValueCalculator(attributes, level, modifier);
                return modifier.serialize(calculator, attributes);
            }),
            total: this.getTotal(totalCalculator),
            totalPerLevel: this.getTotalPerLevel(level),
        };
    }
    getTotalPerLevel(level) {
        const isFirstLevel = level === Level_1.Level.one;
        return this.modifiers
            .reduce((acc, modifier) => acc + (isFirstLevel && !modifier.includeFirstLevel ? 0 : modifier.getPerLevelValue()), 0);
    }
}
exports.PerLevelModifiersList = PerLevelModifiersList;
