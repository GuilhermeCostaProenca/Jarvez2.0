"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ElvenSensesEffect = void 0;
const Ability_1 = require("../../Ability");
const AddFixedModifierToSkill_1 = require("../../Action/AddFixedModifierToSkill");
const ChangeVision_1 = require("../../Action/ChangeVision");
const Modifier_1 = require("../../Modifier");
const Vision_1 = require("../../Sheet/Vision");
const Skill_1 = require("../../Skill");
const RaceAbilityName_1 = require("../RaceAbilityName");
class ElvenSensesEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.elvenSenses);
        this.description = 'Você recebe visão penumbra e +2 em Misticismo e Percepção.';
    }
    apply(transaction) {
        transaction.run(new ChangeVision_1.ChangeVision({
            payload: {
                vision: Vision_1.Vision.penumbra,
                source: this.source,
            },
            transaction,
        }));
        const skillsModifier = new Modifier_1.FixedModifier(this.source, 2);
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                skill: Skill_1.SkillName.mysticism,
                modifier: skillsModifier,
            },
            transaction,
        }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                skill: Skill_1.SkillName.perception,
                modifier: skillsModifier,
            },
            transaction,
        }));
    }
}
exports.ElvenSensesEffect = ElvenSensesEffect;
