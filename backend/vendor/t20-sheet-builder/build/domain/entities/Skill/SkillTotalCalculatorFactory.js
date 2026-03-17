"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SkillTotalCalculatorFactory = void 0;
const ContextualModifiersListTotalCalculator_1 = require("../Modifier/ContextualModifier/ContextualModifiersListTotalCalculator");
const FixedModifiersListTotalCalculator_1 = require("../Modifier/FixedModifier/FixedModifiersListTotalCalculator");
const SkillBaseCalculator_1 = require("./SkillBaseCalculator");
const SkillTotalCalculator_1 = require("./SkillTotalCalculator");
class SkillTotalCalculatorFactory {
    static make(attributes, level, context) {
        const baseCalculator = new SkillBaseCalculator_1.SkillBaseCalculator(level, attributes);
        const fixedCalculator = new FixedModifiersListTotalCalculator_1.FixedModifiersListTotalCalculator(attributes);
        const contextualCalculator = new ContextualModifiersListTotalCalculator_1.ContextualModifiersListTotalCalculator(context, attributes);
        return new SkillTotalCalculator_1.SkillTotalCalculator(baseCalculator, contextualCalculator, fixedCalculator);
    }
}
exports.SkillTotalCalculatorFactory = SkillTotalCalculatorFactory;
