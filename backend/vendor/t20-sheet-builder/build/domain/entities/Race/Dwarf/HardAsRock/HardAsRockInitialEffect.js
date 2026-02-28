"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HardAsRockInitialEffect = void 0;
const PassiveEffect_1 = require("../../../Ability/PassiveEffect");
const AddFixedModifierToLifePoints_1 = require("../../../Action/AddFixedModifierToLifePoints");
const FixedModifier_1 = require("../../../Modifier/FixedModifier/FixedModifier");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class HardAsRockInitialEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você recebe +3 pontos de vida no 1º nível';
    }
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.hardAsRock);
    }
    apply(transaction) {
        const modifier = new FixedModifier_1.FixedModifier(this.source, 3);
        transaction.run(new AddFixedModifierToLifePoints_1.AddFixedModifierToLifePoints({
            payload: {
                modifier,
            },
            transaction,
        }));
    }
}
exports.HardAsRockInitialEffect = HardAsRockInitialEffect;
