"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FearOfHeightsEffect = void 0;
const Ability_1 = require("../../Ability");
const RaceAbilityName_1 = require("../RaceAbilityName");
class FearOfHeightsEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.fearOfHeights);
        this.description = 'Se estiver adjacente a '
            + 'uma queda de 3m ou mais '
            + 'de altura (como um buraco ou '
            + 'penhasco), você fica abalado.';
    }
    apply(transaction) {
        console.log('FearOfHeightsEffect.apply not implemented yet');
    }
}
exports.FearOfHeightsEffect = FearOfHeightsEffect;
