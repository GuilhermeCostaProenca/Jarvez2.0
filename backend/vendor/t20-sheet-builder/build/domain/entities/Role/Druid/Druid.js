"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Druid = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const FaithfulDevote_1 = require("../Cleric/FaithfulDevote/FaithfulDevote");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const DruidSpells_1 = require("./DruidSpells/DruidSpells");
const WildEmpathy_1 = require("./WildEmpathy/WildEmpathy");
class Druid extends Role_1.Role {
    constructor(chosenSkills, chosenSpells, chosenSchools) {
        super(chosenSkills, Druid.selectSkillGroups);
        this.initialLifePoints = Druid.initialLifePoints;
        this.lifePointsPerLevel = Druid.lifePointsPerLevel;
        this.manaPerLevel = Druid.manaPerLevel;
        this.mandatorySkills = Druid.mandatorySkills;
        this.proficiencies = Druid.proficiencies;
        this.name = Druid.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.clericFaithfulDevote]: new FaithfulDevote_1.FaithfulDevote('druid'),
                [RoleAbilityName_1.RoleAbilityName.wildEmpathy]: new WildEmpathy_1.WildEmpathy(),
                [RoleAbilityName_1.RoleAbilityName.druidSpells]: new DruidSpells_1.DruidSpells(chosenSpells, chosenSchools),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Druid = Druid;
Druid.selectSkillGroups = [
    {
        amount: 4,
        skills: [
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.cure,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intuition,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.mysticism,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.religion,
        ],
    },
];
Druid.initialLifePoints = 16;
Druid.lifePointsPerLevel = 4;
Druid.manaPerLevel = 4;
Druid.mandatorySkills = [Skill_1.SkillName.survival, Skill_1.SkillName.will];
Druid.proficiencies = [Sheet_1.Proficiency.shield];
Druid.roleName = RoleName_1.RoleName.druid;
