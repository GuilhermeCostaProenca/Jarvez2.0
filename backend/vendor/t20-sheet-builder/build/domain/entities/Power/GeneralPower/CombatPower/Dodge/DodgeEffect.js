"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DodgeEffect = void 0;
const PassiveEffect_1 = require("../../../../Ability/PassiveEffect");
const AddFixedModifierToDefense_1 = require("../../../../Action/AddFixedModifierToDefense");
const AddFixedModifierToSkill_1 = require("../../../../Action/AddFixedModifierToSkill");
const FixedModifier_1 = require("../../../../Modifier/FixedModifier/FixedModifier");
const SkillName_1 = require("../../../../Skill/SkillName");
const GeneralPowerName_1 = require("../../GeneralPowerName");
class DodgeEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return DodgeEffect.description;
    }
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.dodge);
    }
    apply(transaction) {
        const modifier = new FixedModifier_1.FixedModifier(this.source, 2);
        transaction.run(new AddFixedModifierToDefense_1.AddFixedModifierToDefense({ payload: { modifier }, transaction }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({ payload: { modifier, skill: SkillName_1.SkillName.reflexes }, transaction }));
    }
}
exports.DodgeEffect = DodgeEffect;
DodgeEffect.description = 'Você recebe +2 na Defesa e Reflexos.';
