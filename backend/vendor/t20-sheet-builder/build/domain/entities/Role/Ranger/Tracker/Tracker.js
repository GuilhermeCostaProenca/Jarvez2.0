"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Tracker = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const TrackerEffect_1 = require("./TrackerEffect");
class Tracker extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.tracker);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new TrackerEffect_1.TrackerEffect(),
            },
        });
    }
}
exports.Tracker = Tracker;
