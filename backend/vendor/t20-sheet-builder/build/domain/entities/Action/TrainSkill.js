"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TrainSkill = void 0;
const Skill_1 = require("../Skill/Skill");
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class TrainSkill extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'trainSkill' }));
    }
    execute() {
        const sheetSkills = this.transaction.sheet.getSheetSkills();
        sheetSkills.trainSkill(this.payload.skill);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const skill = Translator_1.Translator.getSkillTranslation(this.payload.skill);
        const trainingBonus = Skill_1.Skill.calculateTrainedPoints(this.transaction.sheet.getLevel());
        return `${source}: perícia ${skill} treinada, bônus de treino ${trainingBonus}.`;
    }
}
exports.TrainSkill = TrainSkill;
