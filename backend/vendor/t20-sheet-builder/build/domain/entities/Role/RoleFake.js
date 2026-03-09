"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleFake = void 0;
const vitest_1 = require("vitest");
const RoleName_1 = require("./RoleName");
const RoleAbilitiesPerLevelFactory_1 = require("./RoleAbilitiesPerLevelFactory");
class RoleFake {
    constructor() {
        this.chosenSkills = [];
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({});
        this.initialLifePoints = 10;
        this.lifePointsPerLevel = 5;
        this.manaPerLevel = 5;
        this.mandatorySkills = [];
        this.selectSkillGroups = [];
        this.proficiencies = [];
        this.name = RoleName_1.RoleName.warrior;
        this.startsWithArmor = true;
        this.getTotalInitialSkills = vitest_1.vi.fn(() => 5);
        this.addToSheet = vitest_1.vi.fn();
        this.serialize = vitest_1.vi.fn();
    }
}
exports.RoleFake = RoleFake;
