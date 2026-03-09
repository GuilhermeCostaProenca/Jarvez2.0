"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PreyMarkEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class PreyMarkEffect extends Ability_1.ActivateableAbilityEffect {
    constructor() {
        super({
            duration: 'scene',
            execution: 'moviment',
            source: RoleAbilityName_1.RoleAbilityName.preyMark,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.description = 'Você pode gastar uma ação'
            + ' de movimento e 1 PM para analisar uma criatura em'
            + ' alcance curto. Até o fim da cena, você recebe +1d4'
            + ' nas rolagens de dano contra essa criatura. A cada'
            + ' quatro níveis, você pode gastar +1 PM para aumentar'
            + ' o bônus de dano (veja a tabela da classe).';
    }
}
exports.PreyMarkEffect = PreyMarkEffect;
