"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeroCode = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class HeroCode extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.heroCode);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(RoleAbilityName_1.RoleAbilityName.heroCode, HeroCode.description),
            },
        });
    }
}
exports.HeroCode = HeroCode;
HeroCode.description = 'Você deve sempre manter'
    + ' sua palavra e nunca pode recusar um pedido de'
    + ' ajuda de alguém inocente. Além disso, nunca pode'
    + ' mentir, trapacear ou roubar. Se violar o código, você'
    + ' perde todos os seus PM e só pode recuperá-los a'
    + ' partir do próximo dia.';
