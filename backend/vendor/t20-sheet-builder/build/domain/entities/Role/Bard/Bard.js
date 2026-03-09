"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Bard = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const BardSpells_1 = require("./BardSpells/BardSpells");
const Inspiration_1 = require("./Inspiration/Inspiration");
class Bard extends Role_1.Role {
    constructor(chosenSkills, chosenSchools, chosenSpells) {
        super(chosenSkills, Bard.selectSkillGroups);
        this.initialLifePoints = Bard.initialLifePoints;
        this.lifePointsPerLevel = Bard.lifePointsPerLevel;
        this.manaPerLevel = Bard.manaPerLevel;
        this.mandatorySkills = Bard.mandatorySkills;
        this.proficiencies = Bard.proficiencies;
        this.name = Bard.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.inspiration]: new Inspiration_1.Inspiration(),
                [RoleAbilityName_1.RoleAbilityName.bardSpells]: new BardSpells_1.BardSpells(new Set(chosenSchools), chosenSpells),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Bard = Bard;
Bard.roleName = RoleName_1.RoleName.bard;
Bard.initialLifePoints = 12;
Bard.lifePointsPerLevel = 3;
Bard.manaPerLevel = 4;
Bard.mandatorySkills = [Skill_1.SkillName.acting, Skill_1.SkillName.reflexes];
Bard.proficiencies = [Sheet_1.Proficiency.martial];
Bard.selectSkillGroups = [
    {
        amount: 6,
        skills: [
            Skill_1.SkillName.acrobatics,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.cheat,
            Skill_1.SkillName.stealth,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intuition,
            Skill_1.SkillName.investigation,
            Skill_1.SkillName.gambling,
            Skill_1.SkillName.thievery,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.mysticism,
            Skill_1.SkillName.nobility,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
            Skill_1.SkillName.will,
        ],
    },
];
