"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SonOfTormenta = void 0;
const Ability_1 = require("../../../Ability");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const SonOfTormentaEffect_1 = require("./SonOfTormentaEffect");
class SonOfTormenta extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.sonOfTormenta);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new SonOfTormentaEffect_1.SonOfTormentaEffect(),
            },
        });
    }
}
exports.SonOfTormenta = SonOfTormenta;
