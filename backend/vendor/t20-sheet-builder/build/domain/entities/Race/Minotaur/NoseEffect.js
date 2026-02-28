"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NoseEffect = void 0;
const Ability_1 = require("../../Ability");
const RaceAbilityName_1 = require("../RaceAbilityName");
class NoseEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.nose);
        this.description = 'Você tem olfato apurado. '
            + ' Contra inimigos que não possa ver e em alcance curto, '
            + ' você não fica desprevenido e camuflagem '
            + ' total lhe causa apenas '
            + ' 20% de chance de '
            + ' falha.';
    }
    apply(transaction) {
        console.log('NoseEffect.apply not implemented yet');
    }
}
exports.NoseEffect = NoseEffect;
