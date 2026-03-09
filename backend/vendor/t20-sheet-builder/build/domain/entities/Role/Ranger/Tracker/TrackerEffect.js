"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TrackerEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddFixedModifierToSkill_1 = require("../../../Action/AddFixedModifierToSkill");
const Modifier_1 = require("../../../Modifier");
const Skill_1 = require("../../../Skill");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class TrackerEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.tracker);
        this.description = 'Você recebe +2 em Sobrevivência.'
            + ' Além disso, pode se mover com seu deslocamento'
            + ' normal enquanto rastreia sem sofrer penalidades no'
            + ' teste de Sobrevivência.';
    }
    apply(transaction) {
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier: new Modifier_1.FixedModifier(this.source, 2),
                skill: Skill_1.SkillName.survival,
            },
            transaction,
        }));
    }
}
exports.TrackerEffect = TrackerEffect;
