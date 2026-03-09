"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Warrior = void 0;
const Level_1 = require("../../Sheet/Level");
const Proficiency_1 = require("../../Sheet/Proficiency");
const SkillName_1 = require("../../Skill/SkillName");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleName_1 = require("../RoleName");
const SpecialAttack_1 = require("./SpecialAttack/SpecialAttack");
class Warrior extends Role_1.Role {
    static get initialLifePoints() {
        return 20;
    }
    static get lifePointsPerLevel() {
        return 5;
    }
    static get manaPerLevel() {
        return 3;
    }
    constructor(chosenSkills) {
        super(chosenSkills, Warrior.selectSkillGroups);
        this.name = RoleName_1.RoleName.warrior;
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory
            .make({
            [Level_1.Level.one]: {
                specialAttack: new SpecialAttack_1.SpecialAttack(),
            },
        });
        this.initialLifePoints = Warrior.initialLifePoints;
        this.lifePointsPerLevel = Warrior.lifePointsPerLevel;
        this.manaPerLevel = Warrior.manaPerLevel;
        this.mandatorySkills = Warrior.mandatorySkills;
        this.proficiencies = Warrior.proficiencies;
    }
    serializeSpecific() {
        return {
            name: Warrior.roleName,
        };
    }
}
exports.Warrior = Warrior;
Warrior.roleName = RoleName_1.RoleName.warrior;
Warrior.selectSkillGroups = [
    { amount: 1, skills: [SkillName_1.SkillName.fight, SkillName_1.SkillName.aim] },
    { amount: 2, skills: [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.athletics, SkillName_1.SkillName.animalRide, SkillName_1.SkillName.war, SkillName_1.SkillName.initiative, SkillName_1.SkillName.intimidation, SkillName_1.SkillName.fight, SkillName_1.SkillName.craft, SkillName_1.SkillName.perception, SkillName_1.SkillName.aim, SkillName_1.SkillName.reflexes] },
];
Warrior.mandatorySkills = [SkillName_1.SkillName.fortitude];
Warrior.proficiencies = [Proficiency_1.Proficiency.martial, Proficiency_1.Proficiency.shield, Proficiency_1.Proficiency.heavyArmor];
