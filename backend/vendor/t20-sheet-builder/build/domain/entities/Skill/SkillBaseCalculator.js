"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SkillBaseCalculator = void 0;
const Skill_1 = require("./Skill");
class SkillBaseCalculator {
    constructor(level, attributes) {
        this.level = level;
        this.attributes = attributes;
    }
    calculate(attribute, isTrained) {
        const trainingPoints = Skill_1.Skill.calculateTrainingPoints(this.level, isTrained);
        const levelPoints = Skill_1.Skill.calculateLevelPoints(this.level);
        return levelPoints + this.attributes[attribute] + trainingPoints;
    }
}
exports.SkillBaseCalculator = SkillBaseCalculator;
