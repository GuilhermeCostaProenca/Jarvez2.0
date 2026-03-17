"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InspirationEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class InspirationEffect extends Ability_1.ActivateableAbilityEffect {
    constructor() {
        super({
            duration: 'scene',
            execution: 'default',
            source: RoleAbilityName_1.RoleAbilityName.inspiration,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(2)];
        this.description = 'Você pode gastar uma ação padrão'
            + ' e 2 PM para inspirar as pessoas com sua arte. Você e'
            + ' todos os seus aliados em alcance curto ganham +1'
            + ' em testes de perícia até o fim da cena. A cada quatro'
            + ' níveis, pode gastar +2 PM para aumentar o bônus'
            + ' em +1.';
    }
}
exports.InspirationEffect = InspirationEffect;
