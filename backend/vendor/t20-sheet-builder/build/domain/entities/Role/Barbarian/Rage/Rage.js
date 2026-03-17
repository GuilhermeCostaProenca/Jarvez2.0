"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Rage = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const RageEffect_1 = require("./RageEffect");
class Rage extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.rage);
        this.effects = new Ability_1.AbilityEffects({
            activateable: {
                default: new RageEffect_1.RageEffect(),
            },
        });
    }
}
exports.Rage = Rage;
