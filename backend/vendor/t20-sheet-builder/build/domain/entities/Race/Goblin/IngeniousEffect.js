"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IngeniousEffect = void 0;
const Ability_1 = require("../../Ability");
const RaceAbilityName_1 = require("../RaceAbilityName");
class IngeniousEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.ingenious);
        this.description = 'Você não sofre penalidades em'
            + ' testes de perícia por não usar ferramentas. Se usar a'
            + ' ferramenta necessária, recebe +2 no teste de perícia.';
    }
    apply(transaction) {
        console.log('IngeniousEffect.apply not implemented yet');
    }
}
exports.IngeniousEffect = IngeniousEffect;
