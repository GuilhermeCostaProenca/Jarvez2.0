"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MagicBloodEffect = void 0;
const Ability_1 = require("../../Ability");
const AddPerLevelModifierToManaPoints_1 = require("../../Action/AddPerLevelModifierToManaPoints");
const Modifier_1 = require("../../Modifier");
const RaceAbilityName_1 = require("../RaceAbilityName");
class MagicBloodEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.magicBlood);
        this.description = 'Você recebe +1 ponto de mana por nível.';
    }
    apply(transaction) {
        const modifier = new Modifier_1.PerLevelModifier({
            source: this.source,
            value: 1,
        });
        transaction.run(new AddPerLevelModifierToManaPoints_1.AddPerLevelModifierToManaPoints({
            payload: {
                modifier,
            },
            transaction,
        }));
    }
}
exports.MagicBloodEffect = MagicBloodEffect;
