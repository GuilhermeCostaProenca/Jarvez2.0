"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageRedCustomTormentaPowersAttributeEffect = void 0;
const PassiveEffect_1 = require("../../../../../../Ability/PassiveEffect");
const ChangeTormentaPowersAttribute_1 = require("../../../../../../Action/ChangeTormentaPowersAttribute");
const RoleAbilityName_1 = require("../../../../../RoleAbilityName");
class ArcanistLineageRedCustomTormentaPowersAttributeEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você pode perder outro atributo em vez de Carisma por poderes da Tormenta';
    }
    constructor(attribute) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
        this.attribute = attribute;
    }
    apply(transaction) {
        transaction.run(new ChangeTormentaPowersAttribute_1.ChangeTormentaPowersAttribute({
            payload: {
                attribute: this.attribute,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.ArcanistLineageRedCustomTormentaPowersAttributeEffect = ArcanistLineageRedCustomTormentaPowersAttributeEffect;
