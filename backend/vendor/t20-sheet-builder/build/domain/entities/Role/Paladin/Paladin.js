"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Paladin = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Blessed_1 = require("./Blessed/Blessed");
const DivineBlow_1 = require("./DivineBlow/DivineBlow");
const HeroCode_1 = require("./HeroCode/HeroCode");
class Paladin extends Role_1.Role {
    constructor(chosenSkills) {
        super(chosenSkills, Paladin.selectSkillGroups);
        this.initialLifePoints = Paladin.initialLifePoints;
        this.lifePointsPerLevel = Paladin.lifePointsPerLevel;
        this.manaPerLevel = Paladin.manaPerLevel;
        this.mandatorySkills = Paladin.mandatorySkills;
        this.proficiencies = Paladin.proficiencies;
        this.name = Paladin.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.blessed]: new Blessed_1.Blessed(),
                [RoleAbilityName_1.RoleAbilityName.heroCode]: new HeroCode_1.HeroCode(),
                [RoleAbilityName_1.RoleAbilityName.divineBlow]: new DivineBlow_1.DivineBlow(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Paladin = Paladin;
Paladin.selectSkillGroups = [
    {
        amount: 2,
        skills: [
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.cure,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.war,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intuition,
            Skill_1.SkillName.nobility,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.religion,
        ],
    },
];
Paladin.initialLifePoints = 20;
Paladin.lifePointsPerLevel = 5;
Paladin.manaPerLevel = 3;
Paladin.mandatorySkills = [Skill_1.SkillName.fight, Skill_1.SkillName.will];
Paladin.proficiencies = [Sheet_1.Proficiency.martial, Sheet_1.Proficiency.heavyArmor, Sheet_1.Proficiency.shield];
Paladin.roleName = RoleName_1.RoleName.paladin;
