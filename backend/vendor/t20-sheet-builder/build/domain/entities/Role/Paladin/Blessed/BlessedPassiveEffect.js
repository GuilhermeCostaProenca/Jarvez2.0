"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BlessedPassiveEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddFixedModifierToManaPoints_1 = require("../../../Action/AddFixedModifierToManaPoints");
const ChangeGrantPowersCount_1 = require("../../../Action/ChangeGrantPowersCount");
const Modifier_1 = require("../../../Modifier");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class BlessedPassiveEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.blessed);
        this.description = 'Você soma seu Carisma no seu'
            + ' total de pontos de mana no 1º nível.';
    }
    apply(transaction) {
        const modifier = new Modifier_1.FixedModifier(RoleAbilityName_1.RoleAbilityName.blessed, 0, new Set(['charisma']));
        transaction.run(new AddFixedModifierToManaPoints_1.AddFixedModifierToManaPoints({
            payload: {
                modifier,
            },
            transaction,
        }));
        transaction.run(new ChangeGrantPowersCount_1.ChangeGrantPowersCount({
            payload: {
                count: 2,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.BlessedPassiveEffect = BlessedPassiveEffect;
