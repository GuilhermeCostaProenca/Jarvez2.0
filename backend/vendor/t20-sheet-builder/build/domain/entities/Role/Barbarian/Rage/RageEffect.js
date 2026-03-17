"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RageEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class RageEffect extends Ability_1.ActivateableAbilityEffect {
    constructor() {
        super({
            duration: 'scene',
            execution: 'free',
            source: RoleAbilityName_1.RoleAbilityName.rage,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(2)];
        this.description = 'Você pode gastar 2 PM para invocar'
            + ' uma fúria selvagem. Você recebe +2 em testes de'
            + ' ataque e rolagens de dano corpo a corpo, mas não'
            + ' pode fazer nenhuma ação que exija calma e concentração'
            + ' (como usar a perícia Furtividade ou lançar'
            + ' magias). A cada cinco níveis, pode gastar +1 PM'
            + ' para aumentar os bônus em +1.';
    }
}
exports.RageEffect = RageEffect;
