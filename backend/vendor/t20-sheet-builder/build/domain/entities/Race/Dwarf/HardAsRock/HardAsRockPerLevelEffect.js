"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HardAsRockPerLevelEffect = void 0;
const PassiveEffect_1 = require("../../../Ability/PassiveEffect");
const AddPerLevelModifierToLifePoints_1 = require("../../../Action/AddPerLevelModifierToLifePoints");
const PerLevelModifier_1 = require("../../../Modifier/PerLevelModifier/PerLevelModifier");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class HardAsRockPerLevelEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você recebe +1 de vida por nível após o primeiro';
    }
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.hardAsRock);
    }
    apply(transaction) {
        transaction.run(new AddPerLevelModifierToLifePoints_1.AddPerLevelModifierToLifePoints({
            payload: {
                modifier: new PerLevelModifier_1.PerLevelModifier({
                    source: this.source,
                    value: 1,
                    includeFirstLevel: false,
                }),
            },
            transaction,
        }));
    }
}
exports.HardAsRockPerLevelEffect = HardAsRockPerLevelEffect;
