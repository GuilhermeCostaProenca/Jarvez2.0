"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SlowAndAlways = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const SlowAndAlwaysEffect_1 = require("./SlowAndAlwaysEffect");
class SlowAndAlways extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.slowAndAlways);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new SlowAndAlwaysEffect_1.SlowAndAlwaysEffect(),
            },
        });
    }
}
exports.SlowAndAlways = SlowAndAlways;
