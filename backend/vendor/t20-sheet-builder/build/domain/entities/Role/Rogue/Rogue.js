"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Rogue = void 0;
const Sheet_1 = require("../../Sheet");
const Skill_1 = require("../../Skill");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const SneakAttack_1 = require("./SneakAttack/SneakAttack");
const Specialist_1 = require("./Specialist/Specialist");
class Rogue extends Role_1.Role {
    constructor(chosenSkills, specialistSkills) {
        super(chosenSkills, Rogue.selectSkillGroups);
        this.initialLifePoints = Rogue.initialLifePoints;
        this.lifePointsPerLevel = Rogue.lifePointsPerLevel;
        this.manaPerLevel = Rogue.manaPerLevel;
        this.mandatorySkills = Rogue.mandatorySkills;
        this.proficiencies = Rogue.proficiencies;
        this.name = Rogue.roleName;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Sheet_1.Level.one]: {
                [RoleAbilityName_1.RoleAbilityName.sneakAttack]: new SneakAttack_1.SneakAttack(),
                [RoleAbilityName_1.RoleAbilityName.specialist]: new Specialist_1.Specialist(specialistSkills),
            },
        });
    }
    serializeSpecific() {
        return {
            name: this.name,
        };
    }
}
exports.Rogue = Rogue;
Rogue.selectSkillGroups = [
    {
        amount: 8,
        skills: [
            Skill_1.SkillName.acrobatics,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.acting,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.cheat,
            Skill_1.SkillName.stealth,
            Skill_1.SkillName.intuition,
            Skill_1.SkillName.intimidation,
            Skill_1.SkillName.investigation,
            Skill_1.SkillName.gambling,
            Skill_1.SkillName.fight,
            Skill_1.SkillName.craft,
            Skill_1.SkillName.perception,
            Skill_1.SkillName.piloting,
            Skill_1.SkillName.aim,
        ],
    },
];
Rogue.initialLifePoints = 12;
Rogue.lifePointsPerLevel = 3;
Rogue.manaPerLevel = 4;
Rogue.mandatorySkills = [Skill_1.SkillName.thievery, Skill_1.SkillName.reflexes];
Rogue.proficiencies = [];
Rogue.roleName = RoleName_1.RoleName.rogue;
