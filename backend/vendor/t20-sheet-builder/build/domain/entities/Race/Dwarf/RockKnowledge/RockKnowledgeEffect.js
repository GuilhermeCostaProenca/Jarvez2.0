"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RockKnowledgeEffect = void 0;
const PassiveEffect_1 = require("../../../Ability/PassiveEffect");
const AddContextualModifierToSkill_1 = require("../../../Action/AddContextualModifierToSkill");
const ChangeVision_1 = require("../../../Action/ChangeVision");
const ContextualModifier_1 = require("../../../Modifier/ContextualModifier/ContextualModifier");
const Vision_1 = require("../../../Sheet/Vision");
const SkillName_1 = require("../../../Skill/SkillName");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class RockKnowledgeEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você recebe visão no escuro e +2 em testes de Percepção e Sobrevivência realizados no subterrâneo.';
    }
    static get skillModifier() {
        return 2;
    }
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
    }
    apply(transaction) {
        const modifier = new ContextualModifier_1.ContextualModifier({
            source: this.source,
            value: RockKnowledgeEffect.skillModifier,
            condition: RockKnowledgeEffect.condition,
        });
        transaction.run(new ChangeVision_1.ChangeVision({ payload: { source: this.source, vision: Vision_1.Vision.dark }, transaction }));
        transaction.run(new AddContextualModifierToSkill_1.AddContextualModifierToSkill({ payload: { modifier, skill: SkillName_1.SkillName.perception }, transaction }));
        transaction.run(new AddContextualModifierToSkill_1.AddContextualModifierToSkill({ payload: { modifier, skill: SkillName_1.SkillName.survival }, transaction }));
    }
}
exports.RockKnowledgeEffect = RockKnowledgeEffect;
RockKnowledgeEffect.condition = {
    description: 'testes devem ser realizados no subterrâneo',
    verify: (context) => { var _a, _b; return (_b = (_a = context.getCurrentLocation()) === null || _a === void 0 ? void 0 : _a.isUnderground) !== null && _b !== void 0 ? _b : false; },
};
