"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageFaerieCheatTrainingEffect = void 0;
const PassiveEffect_1 = require("../../../../../../Ability/PassiveEffect");
const TrainSkill_1 = require("../../../../../../Action/TrainSkill");
const Skill_1 = require("../../../../../../Skill");
const RoleAbilityName_1 = require("../../../../../RoleAbilityName");
class ArcanistLineageFaerieCheatTrainingEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você se torna treinado em Enganação';
    }
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
    }
    apply(transaction) {
        transaction.run(new TrainSkill_1.TrainSkill({
            payload: {
                skill: Skill_1.SkillName.cheat,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.ArcanistLineageFaerieCheatTrainingEffect = ArcanistLineageFaerieCheatTrainingEffect;
