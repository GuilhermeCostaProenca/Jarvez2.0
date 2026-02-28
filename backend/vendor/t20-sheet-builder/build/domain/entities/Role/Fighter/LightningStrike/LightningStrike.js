"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightningStrike = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const LightningStrikeEffect_1 = require("./LightningStrikeEffect");
class LightningStrike extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.lightningStrike);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new LightningStrikeEffect_1.LightningStrikeEffect(),
            },
        });
    }
}
exports.LightningStrike = LightningStrike;
