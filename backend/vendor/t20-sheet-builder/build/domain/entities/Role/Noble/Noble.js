"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Noble = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Asset_1 = require("./Asset/Asset");
const SelfConfidence_1 = require("./SelfConfidence/SelfConfidence");
class Noble extends Role_1.Role {
    constructor(chosenSkills) {
        super(chosenSkills, Noble.selectSkillGroups);
        this.initialLifePoints = Noble.initialLifePoints;
        this.lifePointsPerLevel = Noble.lifePointsPerLevel;
        this.manaPerLevel = Noble.manaPerLevel;
        this.mandatorySkills = Noble.mandatorySkills;
        this.proficiencies = Noble.proficiencies;
        this.name = Noble.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.selfConfidence]: new SelfConfidence_1.SelfConfidence(),
                [RoleAbilityName_1.RoleAbilityName.asset]: new Asset_1.Asset(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Noble = Noble;
Noble.selectSkillGroups = [
    {
        amount: 1,
        skills: [
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.intimidation,
        ],
    },
    {
        amount: 4,
        skills: [
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.acting,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.cheat,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.war,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intimidation,
            Skill_1.SkillName.intuition,
            Skill_1.SkillName.investigation,
            Skill_1.SkillName.gambling,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.nobility,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
        ],
    },
];
Noble.initialLifePoints = 16;
Noble.lifePointsPerLevel = 4;
Noble.manaPerLevel = 4;
Noble.mandatorySkills = [Skill_1.SkillName.will];
Noble.proficiencies = [
    Sheet_1.Proficiency.martial,
    Sheet_1.Proficiency.heavyArmor,
    Sheet_1.Proficiency.shield,
];
Noble.roleName = RoleName_1.RoleName.noble;
