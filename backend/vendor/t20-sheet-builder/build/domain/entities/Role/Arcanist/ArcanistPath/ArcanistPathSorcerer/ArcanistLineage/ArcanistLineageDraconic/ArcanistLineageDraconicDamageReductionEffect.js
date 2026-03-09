"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageDraconicDamageReductionEffect = void 0;
const PassiveEffect_1 = require("../../../../../../Ability/PassiveEffect");
const RoleAbilityName_1 = require("../../../../../RoleAbilityName");
class ArcanistLineageDraconicDamageReductionEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você recebe redução de dano 5 ao tipo escolhido';
    }
    constructor(damageType) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
        this.damageType = damageType;
    }
    apply(transaction) {
        console.log('TODO: ArcanistLineageDraconicDamageReductionEffect.apply()');
    }
}
exports.ArcanistLineageDraconicDamageReductionEffect = ArcanistLineageDraconicDamageReductionEffect;
