"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SlenderPlage = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const SlenderPlageEffect_1 = require("./SlenderPlageEffect");
class SlenderPlage extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.slenderPlage);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new SlenderPlageEffect_1.SlenderPlageEffect(),
            },
        });
    }
}
exports.SlenderPlage = SlenderPlage;
