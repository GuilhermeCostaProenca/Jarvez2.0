"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GloriennGraceEffect = void 0;
const Ability_1 = require("../../Ability");
const ChangeDisplacement_1 = require("../../Action/ChangeDisplacement");
const RaceAbilityName_1 = require("../RaceAbilityName");
class GloriennGraceEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.gloriennGrace);
        this.description = 'Seu deslocamento é 12m (em vez de 9m).';
    }
    apply(transaction) {
        transaction.run(new ChangeDisplacement_1.ChangeDisplacement({
            payload: {
                displacement: 12,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.GloriennGraceEffect = GloriennGraceEffect;
