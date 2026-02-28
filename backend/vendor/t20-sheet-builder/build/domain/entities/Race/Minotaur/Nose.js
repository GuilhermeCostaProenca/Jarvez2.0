"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Nose = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const NoseEffect_1 = require("./NoseEffect");
class Nose extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.nose);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new NoseEffect_1.NoseEffect(),
            },
        });
    }
}
exports.Nose = Nose;
