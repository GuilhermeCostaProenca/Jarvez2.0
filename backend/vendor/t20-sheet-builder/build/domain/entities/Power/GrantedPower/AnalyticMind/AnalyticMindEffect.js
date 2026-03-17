"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnalyticMindEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddFixedModifierToSkill_1 = require("../../../Action/AddFixedModifierToSkill");
const Modifier_1 = require("../../../Modifier");
const Skill_1 = require("../../../Skill");
const GrantedPowerName_1 = require("../GrantedPowerName");
class AnalyticMindEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(GrantedPowerName_1.GrantedPowerName.analyticMind);
        this.description = AnalyticMindEffect.description;
    }
    apply(transaction) {
        const modifier = new Modifier_1.FixedModifier(this.source, 2);
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier,
                skill: Skill_1.SkillName.intuition,
            },
            transaction,
        }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier,
                skill: Skill_1.SkillName.investigation,
            },
            transaction,
        }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier,
                skill: Skill_1.SkillName.will,
            },
            transaction,
        }));
    }
}
exports.AnalyticMindEffect = AnalyticMindEffect;
AnalyticMindEffect.description = 'Você recebe +2 em Intuição, Investigação e Vontade.';
