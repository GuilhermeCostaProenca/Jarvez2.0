"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Audacity = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const AudacityEffect_1 = require("./AudacityEffect");
class Audacity extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.audacity);
        this.effects = new Ability_1.AbilityEffects({
            triggered: {
                default: new AudacityEffect_1.AudacityEffect(),
            },
        });
    }
}
exports.Audacity = Audacity;
