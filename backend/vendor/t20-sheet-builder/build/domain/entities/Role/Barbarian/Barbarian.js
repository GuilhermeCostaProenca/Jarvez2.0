"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Barbarian = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleName_1 = require("../RoleName");
const Rage_1 = require("./Rage/Rage");
class Barbarian extends Role_1.Role {
    constructor(chosenSkills = []) {
        super(chosenSkills, Barbarian.selectSkillGroups);
        this.initialLifePoints = Barbarian.initialLifePoints;
        this.lifePointsPerLevel = Barbarian.lifePointsPerLevel;
        this.manaPerLevel = Barbarian.manaPerLevel;
        this.mandatorySkills = Barbarian.mandatorySkills;
        this.proficiencies = Barbarian.proficiencies;
        this.name = Barbarian.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                rage: new Rage_1.Rage(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: Barbarian.roleName,
        };
    }
}
exports.Barbarian = Barbarian;
Barbarian.roleName = RoleName_1.RoleName.barbarian;
Barbarian.selectSkillGroups = [
    { amount: 4, skills: [
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intimidation,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
            Skill_1.SkillName.survival,
            Skill_1.SkillName.will,
        ] },
];
Barbarian.initialLifePoints = 24;
Barbarian.lifePointsPerLevel = 6;
Barbarian.manaPerLevel = 3;
Barbarian.mandatorySkills = [Skill_1.SkillName.fight, Skill_1.SkillName.fortitude];
Barbarian.proficiencies = [Sheet_1.Proficiency.martial, Sheet_1.Proficiency.shield];
