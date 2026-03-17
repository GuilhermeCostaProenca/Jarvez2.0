"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageDraconicCharismaBonusEffect = void 0;
const PassiveEffect_1 = require("../../../../../../Ability/PassiveEffect");
const AddFixedModifierToLifePoints_1 = require("../../../../../../Action/AddFixedModifierToLifePoints");
const FixedModifier_1 = require("../../../../../../Modifier/FixedModifier/FixedModifier");
const RoleAbilityName_1 = require("../../../../../RoleAbilityName");
class ArcanistLineageDraconicCharismaBonusEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você soma seu Carisma em seus pontos de vida iniciais';
    }
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
    }
    apply(transaction) {
        transaction.run(new AddFixedModifierToLifePoints_1.AddFixedModifierToLifePoints({
            payload: {
                modifier: new FixedModifier_1.FixedModifier(this.source, 0, new Set(['charisma'])),
            },
            transaction,
        }));
    }
}
exports.ArcanistLineageDraconicCharismaBonusEffect = ArcanistLineageDraconicCharismaBonusEffect;
