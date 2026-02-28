"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TrainIntelligenceSkills = void 0;
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class TrainIntelligenceSkills extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'trainIntelligenceSkills' }));
    }
    execute() {
        const sheetSkills = this.transaction.sheet.getSheetSkills();
        sheetSkills.trainIntelligenceSkills(this.payload.skills);
    }
    getDescription() {
        const { skills } = this.payload;
        const trainedSkills = skills.map(skill => Translator_1.Translator.getSkillTranslation(skill)).join(', ');
        return skills.length
            ? `Perícias treinadas pela inteligência: ${trainedSkills}.`
            : 'Nenhuma perícia treinada pela inteligência.';
    }
}
exports.TrainIntelligenceSkills = TrainIntelligenceSkills;
