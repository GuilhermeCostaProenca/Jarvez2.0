"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Inventor = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Ingenuity_1 = require("./Ingenuity/Ingenuity");
const Prototype_1 = require("./Prototype/Prototype");
class Inventor extends Role_1.Role {
    constructor(chosenSkills, prototypeParams) {
        super(chosenSkills, Inventor.selectSkillGroups);
        this.initialLifePoints = Inventor.initialLifePoints;
        this.lifePointsPerLevel = Inventor.lifePointsPerLevel;
        this.manaPerLevel = Inventor.manaPerLevel;
        this.mandatorySkills = Inventor.mandatorySkills;
        this.proficiencies = Inventor.proficiencies;
        this.name = Inventor.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.ingenuity]: new Ingenuity_1.Ingenuity(),
                [RoleAbilityName_1.RoleAbilityName.prototype]: new Prototype_1.Prototype(prototypeParams),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Inventor = Inventor;
Inventor.selectSkillGroups = [
    {
        amount: 4,
        skills: [
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.cure,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.fortitude,
            Skill_1.SkillName.initiative,
            Skill_1.SkillName.investigation,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.mysticism,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.piloting,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.aim,
        ],
    },
];
Inventor.initialLifePoints = 12;
Inventor.lifePointsPerLevel = 3;
Inventor.manaPerLevel = 4;
Inventor.mandatorySkills = [Skill_1.SkillName.craft, Skill_1.SkillName.will];
Inventor.proficiencies = [];
Inventor.roleName = RoleName_1.RoleName.inventor;
