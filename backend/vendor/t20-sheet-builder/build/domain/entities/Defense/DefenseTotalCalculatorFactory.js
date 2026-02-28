"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefenseTotalCalculatorFactory = void 0;
const FixedModifiersListTotalCalculator_1 = require("../Modifier/FixedModifier/FixedModifiersListTotalCalculator");
const DefenseBaseCalculator_1 = require("./DefenseBaseCalculator");
const DefenseTotalCalculator_1 = require("./DefenseTotalCalculator");
class DefenseTotalCalculatorFactory {
    static make(attributes, armorBonus, shieldBonus) {
        const baseCalculator = new DefenseBaseCalculator_1.DefenseBaseCalculator(attributes, armorBonus, shieldBonus);
        const fixedCalculator = new FixedModifiersListTotalCalculator_1.FixedModifiersListTotalCalculator(attributes);
        return new DefenseTotalCalculator_1.DefenseTotalCalculator(baseCalculator, fixedCalculator);
    }
}
exports.DefenseTotalCalculatorFactory = DefenseTotalCalculatorFactory;
