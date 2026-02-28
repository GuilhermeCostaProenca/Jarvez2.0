"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RaceAbilityFake = void 0;
const AbilityEffects_1 = require("../Ability/AbilityEffects");
const RaceAbilityName_1 = require("./RaceAbilityName");
const vitest_1 = require("vitest");
class RaceAbilityFake {
    constructor() {
        this.effects = new AbilityEffects_1.AbilityEffects({});
        this.name = RaceAbilityName_1.RaceAbilityName.versatile;
        this.addToSheet = vitest_1.vi.fn();
        this.abilityType = 'role';
    }
}
exports.RaceAbilityFake = RaceAbilityFake;
