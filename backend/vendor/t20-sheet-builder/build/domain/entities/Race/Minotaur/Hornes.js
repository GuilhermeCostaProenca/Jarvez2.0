"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Hornes = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const HornesEffect_1 = require("./HornesEffect");
class Hornes extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.hornes);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new HornesEffect_1.HornesEffect(),
            },
        });
    }
}
exports.Hornes = Hornes;
