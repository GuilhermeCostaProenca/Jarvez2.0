"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SkillRequirement = void 0;
const Translator_1 = require("../../Translator");
const Requirement_1 = require("./Requirement");
class SkillRequirement extends Requirement_1.Requirement {
    constructor(skill) {
        super();
        this.skill = skill;
        this.description = this.getDescription();
    }
    verify(sheet) {
        const skills = sheet.getSheetSkills().getSkills();
        return skills[this.skill].getIsTrained();
    }
    getDescription() {
        return `Treinado em ${Translator_1.Translator.getSkillTranslation(this.skill)}.`;
    }
}
exports.SkillRequirement = SkillRequirement;
