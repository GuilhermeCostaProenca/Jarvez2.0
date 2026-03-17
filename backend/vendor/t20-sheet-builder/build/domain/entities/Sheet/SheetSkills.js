"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetSkills = void 0;
const InitialSkillsGenerator_1 = require("../Skill/InitialSkillsGenerator");
const SkillTotalCalculatorFactory_1 = require("../Skill/SkillTotalCalculatorFactory");
class SheetSkills {
    constructor(skills = InitialSkillsGenerator_1.InitialSkillsGenerator.generate()) {
        this.skills = skills;
        this.intelligenceSkills = [];
    }
    trainSkill(name) {
        this.skills[name].train();
    }
    getSkill(name) {
        return this.skills[name];
    }
    addContextualModifierTo(skill, modifier) {
        this.skills[skill].addContextualModifier(modifier);
    }
    addFixedModifierTo(skill, modifier) {
        this.skills[skill].addFixedModifier(modifier);
    }
    trainIntelligenceSkills(skills) {
        skills.forEach(skill => {
            this.skills[skill].train();
            this.intelligenceSkills.push(skill);
        });
    }
    getSkills() {
        return this.skills;
    }
    serialize(sheet, context) {
        const attributes = sheet.getSheetAttributes().getValues();
        const level = sheet.getLevel();
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(attributes, level, context);
        const entries = Object.entries(this.skills);
        const serialized = entries.reduce((acc, [skillName, skill]) => {
            acc.skills[skillName] = skill.serialize(calculator, sheet, context);
            return acc;
            // eslint-disable-next-line @typescript-eslint/prefer-reduce-type-parameter
        }, { skills: {}, intelligenceSkills: [] });
        serialized.intelligenceSkills = this.intelligenceSkills;
        return serialized;
    }
}
exports.SheetSkills = SheetSkills;
