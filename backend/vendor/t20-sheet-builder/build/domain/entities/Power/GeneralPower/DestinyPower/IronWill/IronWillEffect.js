"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IronWillEffect = void 0;
const PassiveEffect_1 = require("../../../../Ability/PassiveEffect");
const AddFixedModifierToSkill_1 = require("../../../../Action/AddFixedModifierToSkill");
const AddPerLevelModifierToManaPoints_1 = require("../../../../Action/AddPerLevelModifierToManaPoints");
const FixedModifier_1 = require("../../../../Modifier/FixedModifier/FixedModifier");
const PerLevelModifier_1 = require("../../../../Modifier/PerLevelModifier/PerLevelModifier");
const SkillName_1 = require("../../../../Skill/SkillName");
class IronWillEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return IronWillEffect.description;
    }
    apply(transaction) {
        transaction.run(new AddPerLevelModifierToManaPoints_1.AddPerLevelModifierToManaPoints({
            payload: {
                modifier: new PerLevelModifier_1.PerLevelModifier({
                    source: this.source,
                    value: 1,
                    includeFirstLevel: true,
                    frequency: 2,
                }),
            },
            transaction,
        }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier: new FixedModifier_1.FixedModifier(this.source, 2),
                skill: SkillName_1.SkillName.will,
            },
            transaction,
        }));
    }
}
exports.IronWillEffect = IronWillEffect;
IronWillEffect.description = 'Você recebe +1 PM para cada dois níveis de personagem e +2 em Vontade.';
