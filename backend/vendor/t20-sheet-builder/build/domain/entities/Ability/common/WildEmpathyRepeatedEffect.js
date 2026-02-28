"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WildEmpathyRepeatedEffect = void 0;
const AddFixedModifierToSkill_1 = require("../../Action/AddFixedModifierToSkill");
const Modifier_1 = require("../../Modifier");
const RaceAbilityName_1 = require("../../Race/RaceAbilityName");
const RoleAbilityName_1 = require("../../Role/RoleAbilityName");
const Skill_1 = require("../../Skill");
const PassiveEffect_1 = require("../PassiveEffect");
class WildEmpathyRepeatedEffect extends PassiveEffect_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.wildEmpathy);
        this.description = 'Caso receba esta'
            + ' habilidade novamente,'
            + ' recebe +2 em'
            + ' Adestramento.';
    }
    apply(transaction) {
        const raceAbilities = transaction.sheet.getSheetAbilities().getRaceAbilities();
        const roleAbilities = transaction.sheet.getSheetAbilities().getRoleAbilities();
        if (raceAbilities.has(RaceAbilityName_1.RaceAbilityName.wildEmpathy) || roleAbilities.has(RoleAbilityName_1.RoleAbilityName.wildEmpathy)) {
            transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
                payload: {
                    modifier: new Modifier_1.FixedModifier(this.source, 2),
                    skill: Skill_1.SkillName.animalHandling,
                },
                transaction,
            }));
        }
    }
}
exports.WildEmpathyRepeatedEffect = WildEmpathyRepeatedEffect;
