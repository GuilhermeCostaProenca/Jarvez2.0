"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RolePowerFake = exports.GeneralPowerFake = exports.PowerFake = void 0;
const vitest_1 = require("vitest");
const AbilityEffects_1 = require("../Ability/AbilityEffects");
const RolePowerName_1 = require("../Role/RolePowerName");
const GeneralPowerName_1 = require("./GeneralPower/GeneralPowerName");
const GeneralPower_1 = require("./GeneralPower");
class PowerFake {
    constructor() {
        this.powerType = 'general';
        this.name = GeneralPowerName_1.GeneralPowerName.dodge;
        this.abilityType = 'power';
        this.addToSheet = vitest_1.vi.fn();
        this.verifyRequirements = vitest_1.vi.fn();
        this.effects = new AbilityEffects_1.AbilityEffects({});
    }
}
exports.PowerFake = PowerFake;
class GeneralPowerFake {
    constructor() {
        this.group = GeneralPower_1.GeneralPowerGroup.combat;
        this.powerType = 'general';
        this.name = GeneralPowerName_1.GeneralPowerName.dodge;
        this.abilityType = 'power';
        this.addToSheet = vitest_1.vi.fn();
        this.verifyRequirements = vitest_1.vi.fn();
        this.effects = new AbilityEffects_1.AbilityEffects({});
        this.serialize = vitest_1.vi.fn();
    }
}
exports.GeneralPowerFake = GeneralPowerFake;
class RolePowerFake {
    constructor() {
        this.serialize = vitest_1.vi.fn();
        this.powerType = 'role';
        this.name = RolePowerName_1.RolePowerName.archer;
        this.abilityType = 'power';
        this.verifyRequirements = vitest_1.vi.fn();
        this.addToSheet = vitest_1.vi.fn();
        this.effects = new AbilityEffects_1.AbilityEffects({});
    }
}
exports.RolePowerFake = RolePowerFake;
