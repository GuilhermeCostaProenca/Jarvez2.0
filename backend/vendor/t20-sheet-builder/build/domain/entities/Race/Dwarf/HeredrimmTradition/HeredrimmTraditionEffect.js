"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeredrimmTraditionEffect = void 0;
const Ability_1 = require("../../../Ability");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class HeredrimmTraditionEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.heredrimmTradition);
        this.description = 'Você é perito nas armas tradicionais'
            + ' anãs, seja por ter treinado com elas, seja por usá-las como ferramentas de ofício. Para você,'
            + ' todos os machados, martelos, marretas e picaretas são armas simples.'
            + ' Você recebe +2 em ataques com essas armas.';
    }
    apply(transaction) {
        console.log('HeredrimmTraditionProficiencyEffect.apply not implemented');
    }
}
exports.HeredrimmTraditionEffect = HeredrimmTraditionEffect;
