"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GloriennGrace = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const GloriennGraceEffect_1 = require("./GloriennGraceEffect");
class GloriennGrace extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.gloriennGrace);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new GloriennGraceEffect_1.GloriennGraceEffect(),
            },
        });
    }
}
exports.GloriennGrace = GloriennGrace;
