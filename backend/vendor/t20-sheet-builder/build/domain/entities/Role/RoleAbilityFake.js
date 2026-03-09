"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleAbilityFake = void 0;
const AbilityEffects_1 = require("../Ability/AbilityEffects");
const RoleAbilityName_1 = require("./RoleAbilityName");
const vitest_1 = require("vitest");
class RoleAbilityFake {
    constructor() {
        this.effects = new AbilityEffects_1.AbilityEffects({});
        this.name = RoleAbilityName_1.RoleAbilityName.specialAttack;
        this.addToSheet = vitest_1.vi.fn();
        this.abilityType = 'role';
    }
}
exports.RoleAbilityFake = RoleAbilityFake;
