"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Versatile = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const VersatileEffect_1 = require("./VersatileEffect");
class Versatile extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.versatile);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new VersatileEffect_1.VersatileEffect(),
            },
        });
    }
    addChoice(choice) {
        this.effects.passive.default.addChoice(choice);
    }
}
exports.Versatile = Versatile;
