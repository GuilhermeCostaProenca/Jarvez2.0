"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StreetRat = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const StreetRatEffect_1 = require("./StreetRatEffect");
class StreetRat extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.streetRat);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new StreetRatEffect_1.StreetRatEffect(),
            },
        });
    }
}
exports.StreetRat = StreetRat;
