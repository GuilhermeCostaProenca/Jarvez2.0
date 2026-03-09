"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StreetRatEffect = void 0;
const Ability_1 = require("../../Ability");
const AddFixedModifierToSkill_1 = require("../../Action/AddFixedModifierToSkill");
const Modifier_1 = require("../../Modifier");
const Skill_1 = require("../../Skill");
const RaceAbilityName_1 = require("../RaceAbilityName");
class StreetRatEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.streetRat);
        this.description = 'Você recebe +2 em'
            + ' Fortitude e sua recuperação de PV e PM nunca é'
            + ' inferior ao seu nível.';
    }
    apply(transaction) {
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier: new Modifier_1.FixedModifier(this.source, 2),
                skill: Skill_1.SkillName.fortitude,
            },
            transaction,
        }));
    }
}
exports.StreetRatEffect = StreetRatEffect;
