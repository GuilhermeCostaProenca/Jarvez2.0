"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Ranger = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const PreyMark_1 = require("./PreyMark/PreyMark");
const Tracker_1 = require("./Tracker/Tracker");
class Ranger extends Role_1.Role {
    constructor(chosenSkills) {
        super(chosenSkills, Ranger.selectSkillGroups);
        this.initialLifePoints = Ranger.initialLifePoints;
        this.lifePointsPerLevel = Ranger.lifePointsPerLevel;
        this.manaPerLevel = Ranger.manaPerLevel;
        this.mandatorySkills = Ranger.mandatorySkills;
        this.proficiencies = Ranger.proficiencies;
        this.name = Ranger.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.preyMark]: new PreyMark_1.PreyMark(),
                [RoleAbilityName_1.RoleAbilityName.tracker]: new Tracker_1.Tracker(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Ranger = Ranger;
Ranger.selectSkillGroups = [
    {
        amount: 1,
        skills: [Skill_1.SkillName.fight, Skill_1.SkillName.aim],
    },
    {
        amount: 6,
        skills: [
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.cure,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.stealth,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.investigation,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
            Skill_1.SkillName.reflexes,
        ],
    },
];
Ranger.initialLifePoints = 16;
Ranger.lifePointsPerLevel = 4;
Ranger.manaPerLevel = 4;
Ranger.mandatorySkills = [Skill_1.SkillName.survival];
Ranger.proficiencies = [Sheet_1.Proficiency.martial, Sheet_1.Proficiency.shield];
Ranger.roleName = RoleName_1.RoleName.ranger;
