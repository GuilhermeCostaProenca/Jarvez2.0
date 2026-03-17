"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Fighter = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Fight_1 = require("./Fight/Fight");
const LightningStrike_1 = require("./LightningStrike/LightningStrike");
class Fighter extends Role_1.Role {
    constructor(chosenSkills) {
        super(chosenSkills, Fighter.selectSkillGroups);
        this.initialLifePoints = Fighter.initialLifePoints;
        this.lifePointsPerLevel = Fighter.lifePointsPerLevel;
        this.manaPerLevel = Fighter.manaPerLevel;
        this.mandatorySkills = Fighter.mandatorySkills;
        this.proficiencies = Fighter.proficiencies;
        this.name = Fighter.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.fight]: new Fight_1.Fight(),
                [RoleAbilityName_1.RoleAbilityName.lightningStrike]: new LightningStrike_1.LightningStrike(),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Fighter = Fighter;
Fighter.selectSkillGroups = [
    {
        amount: 4,
        skills: [
            Skill_1.SkillName.acrobatics,
            Skill_1.SkillName.animalHandling,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.cheat,
            Skill_1.SkillName.stealth,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.intimidation,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
            Skill_1.SkillName.reflexes,
        ],
    },
];
Fighter.initialLifePoints = 20;
Fighter.lifePointsPerLevel = 5;
Fighter.manaPerLevel = 3;
Fighter.mandatorySkills = [Skill_1.SkillName.fortitude, Skill_1.SkillName.fight];
Fighter.proficiencies = [];
Fighter.roleName = RoleName_1.RoleName.fighter;
