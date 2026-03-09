"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SneakAttack = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class SneakAttack extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.sneakAttack);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(RoleAbilityName_1.RoleAbilityName.sneakAttack, SneakAttack.description),
            },
        });
    }
}
exports.SneakAttack = SneakAttack;
SneakAttack.description = 'Você sabe atingir os pontos'
    + ' vitais de inimigos distraídos. Uma vez por rodada,'
    + ' quando atinge uma criatura desprevenida com um'
    + ' ataque corpo a corpo ou em alcance curto, ou uma'
    + ' criatura que esteja flanqueando, você causa 1d6 pon-'
    + ' tos de dano extra. A cada dois níveis, esse dano extra'
    + ' aumenta em +1d6. Uma criatura imune a acertos'
    + ' críticos também é imune a ataques furtivos.';
