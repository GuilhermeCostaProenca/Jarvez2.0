"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Knight = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Bulwark_1 = require("./Bulwark/Bulwark");
const HonourCode_1 = require("./HonourCode/HonourCode");
class Knight extends Role_1.Role {
    constructor(chosenSkills) {
        super(chosenSkills, Knight.selectSkillGroups);
        this.initialLifePoints = Knight.initialLifePoints;
        this.lifePointsPerLevel = Knight.lifePointsPerLevel;
        this.manaPerLevel = Knight.manaPerLevel;
        this.mandatorySkills = Knight.mandatorySkills;
        this.proficiencies = Knight.proficiencies;
        this.name = Knight.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.honourCode]: new HonourCode_1.HonourCode(),
                [RoleAbilityName_1.RoleAbilityName.bulwark]: new Bulwark_1.Bulwark(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Knight = Knight;
Knight.selectSkillGroups = [
    {
        amount: 2,
        skills: [
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.war,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intimidation,
            Skill_1.SkillName.nobility,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.will,
        ],
    },
];
Knight.initialLifePoints = 20;
Knight.lifePointsPerLevel = 5;
Knight.manaPerLevel = 3;
Knight.mandatorySkills = [Skill_1.SkillName.fight, Skill_1.SkillName.fortitude];
Knight.proficiencies = [Sheet_1.Proficiency.martial, Sheet_1.Proficiency.heavyArmor, Sheet_1.Proficiency.shield];
Knight.roleName = RoleName_1.RoleName.knight;
