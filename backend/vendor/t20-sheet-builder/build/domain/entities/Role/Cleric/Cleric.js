"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Cleric = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const ClericSpells_1 = require("./ClericSpells/ClericSpells");
const FaithfulDevote_1 = require("./FaithfulDevote/FaithfulDevote");
class Cleric extends Role_1.Role {
    constructor(chosenSkills, chosenSpells) {
        super(chosenSkills, Cleric.selectSkillGroups);
        this.initialLifePoints = Cleric.initialLifePoints;
        this.lifePointsPerLevel = Cleric.lifePointsPerLevel;
        this.manaPerLevel = Cleric.manaPerLevel;
        this.mandatorySkills = Cleric.mandatorySkills;
        this.proficiencies = Cleric.proficiencies;
        this.name = Cleric.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.clericFaithfulDevote]: new FaithfulDevote_1.FaithfulDevote('cleric'),
                [RoleAbilityName_1.RoleAbilityName.clericSpells]: new ClericSpells_1.ClericSpells(chosenSpells),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Cleric = Cleric;
Cleric.selectSkillGroups = [
    {
        amount: 2,
        skills: [
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.cure,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intuition,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.mysticism,
            Skill_1.SkillName.nobility,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
        ],
    },
];
Cleric.initialLifePoints = 16;
Cleric.lifePointsPerLevel = 4;
Cleric.manaPerLevel = 5;
Cleric.mandatorySkills = [Skill_1.SkillName.religion, Skill_1.SkillName.will];
Cleric.proficiencies = [Sheet_1.Proficiency.heavyArmor, Sheet_1.Proficiency.shield];
Cleric.roleName = RoleName_1.RoleName.cleric;
