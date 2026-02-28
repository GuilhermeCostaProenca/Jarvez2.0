"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SkillTotalCalculator = void 0;
const Modifier_1 = require("../Modifier");
class SkillTotalCalculator {
    constructor(baseCalculator, contextualCalculator, fixedCalculator) {
        this.baseCalculator = baseCalculator;
        this.contextualCalculator = contextualCalculator;
        this.fixedCalculator = fixedCalculator;
    }
    calculate(skill) {
        const fixedModifiers = skill.fixedModifiers.clone();
        fixedModifiers.add(new Modifier_1.FixedModifier('default', skill.getAttributeModifier(this.baseCalculator.attributes)));
        fixedModifiers.add(new Modifier_1.FixedModifier('default', skill.getLevelPoints(this.baseCalculator.level)));
        fixedModifiers.add(new Modifier_1.FixedModifier('default', skill.getTrainingPoints(this.baseCalculator.level)));
        const fixedModifiersTotal = fixedModifiers.getTotal(this.fixedCalculator);
        const contextualModifiersTotal = skill.contextualModifiers.getTotal(this.contextualCalculator);
        return contextualModifiersTotal + fixedModifiersTotal;
    }
}
exports.SkillTotalCalculator = SkillTotalCalculator;
