"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageRedExtraTormentaPowerEffect = void 0;
const PassiveEffect_1 = require("../../../../../../Ability/PassiveEffect");
const PickGeneralPower_1 = require("../../../../../../Action/PickGeneralPower");
const RoleAbilityName_1 = require("../../../../../RoleAbilityName");
class ArcanistLineageRedExtraTormentaPowerEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você recebe um poder da Tormenta';
    }
    constructor(power) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
        this.power = power;
    }
    apply(transaction) {
        transaction.run(new PickGeneralPower_1.PickGeneralPower({
            payload: {
                power: this.power,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.ArcanistLineageRedExtraTormentaPowerEffect = ArcanistLineageRedExtraTormentaPowerEffect;
