"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FearOfHeights = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const FearOfHeightsEffect_1 = require("./FearOfHeightsEffect");
class FearOfHeights extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.fearOfHeights);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new FearOfHeightsEffect_1.FearOfHeightsEffect(),
            },
        });
    }
}
exports.FearOfHeights = FearOfHeights;
