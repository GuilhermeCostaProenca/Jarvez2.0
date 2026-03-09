"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FightEffect = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class FightEffect extends Ability_1.RolePlayEffect {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.fight, FightEffect.description);
    }
}
exports.FightEffect = FightEffect;
FightEffect.description = 'Seus ataques desarmados causam'
    + ' 1d6 pontos de dano e podem causar dano letal ou não letal (sem penalidades).'
    + ' A cada quatro níveis, seu dano desarmado aumenta, conforme a tabela.'
    + ' O dano na tabela é para criaturas Pequenas e Médias. Criaturas Minúsculas'
    + ' diminuem esse dano em um passo, Grandes e Enormes aumentam em um passo e Colossais'
    + ' aumentam em dois passos.';
