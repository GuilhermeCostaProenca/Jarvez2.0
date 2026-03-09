"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SlowAndAlwaysEffect = void 0;
const PassiveEffect_1 = require("../../../Ability/PassiveEffect");
const ChangeDisplacement_1 = require("../../../Action/ChangeDisplacement");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class SlowAndAlwaysEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Seu deslocamento é 6m (em vez de 9m).';
    }
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.slowAndAlways);
    }
    apply(transaction) {
        transaction.run(new ChangeDisplacement_1.ChangeDisplacement({
            payload: {
                displacement: 6,
                source: this.source,
            }, transaction,
        }));
    }
}
exports.SlowAndAlwaysEffect = SlowAndAlwaysEffect;
