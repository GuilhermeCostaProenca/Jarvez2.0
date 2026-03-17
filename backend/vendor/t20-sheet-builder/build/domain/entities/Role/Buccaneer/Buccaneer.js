"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Buccaneer = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleName_1 = require("../RoleName");
const Audacity_1 = require("./Audacity/Audacity");
class Buccaneer extends Role_1.Role {
    constructor(chosenSkills = []) {
        super(chosenSkills, Buccaneer.selectSkillGroups);
        this.initialLifePoints = Buccaneer.initialLifePoints;
        this.lifePointsPerLevel = Buccaneer.lifePointsPerLevel;
        this.manaPerLevel = Buccaneer.manaPerLevel;
        this.mandatorySkills = Buccaneer.mandatorySkills;
        this.proficiencies = Buccaneer.proficiencies;
        this.name = Buccaneer.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                audacity: new Audacity_1.Audacity(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: Buccaneer.roleName,
        };
    }
}
exports.Buccaneer = Buccaneer;
Buccaneer.roleName = RoleName_1.RoleName.buccaneer;
Buccaneer.initialLifePoints = 16;
Buccaneer.lifePointsPerLevel = 4;
Buccaneer.manaPerLevel = 3;
Buccaneer.mandatorySkills = [Skill_1.SkillName.reflexes];
Buccaneer.proficiencies = [Sheet_1.Proficiency.martial];
Buccaneer.selectSkillGroups = [
    { amount: 1, skills: [
            Skill_1.SkillName.aim,
            Skill_1.SkillName.fight,
        ] },
    { amount: 4, skills: [
            Skill_1.SkillName.acrobatics,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.acting,
            Skill_1.SkillName.cheat,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.stealth,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intimidation,
            Skill_1.SkillName.gambling,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
            Skill_1.SkillName.piloting,
        ] },
];
