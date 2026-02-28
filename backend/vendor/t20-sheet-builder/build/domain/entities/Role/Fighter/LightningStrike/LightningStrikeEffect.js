"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightningStrikeEffect = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class LightningStrikeEffect extends Ability_1.RolePlayEffect {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.lightningStrike, LightningStrikeEffect.description);
    }
}
exports.LightningStrikeEffect = LightningStrikeEffect;
LightningStrikeEffect.description = 'Quando usa a ação agredir para fazer um ataque desarmado,'
    + ' você pode gastar 1 PM para realizar um ataque desarmado adicional.';
