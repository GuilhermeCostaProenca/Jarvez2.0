"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EmptyMindEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddFixedModifierToSkill_1 = require("../../../Action/AddFixedModifierToSkill");
const Modifier_1 = require("../../../Modifier");
const Skill_1 = require("../../../Skill");
const GrantedPowerName_1 = require("../GrantedPowerName");
class EmptyMindEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(GrantedPowerName_1.GrantedPowerName.emptyMind);
        this.description = EmptyMindEffect.description;
    }
    apply(transaction) {
        const modifier = new Modifier_1.FixedModifier(this.source, 2);
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier,
                skill: Skill_1.SkillName.initiative,
            },
            transaction,
        }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier,
                skill: Skill_1.SkillName.perception,
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
exports.EmptyMindEffect = EmptyMindEffect;
EmptyMindEffect.description = 'Você recebe +2 em Iniciativa, Percepção e Vontade.';
