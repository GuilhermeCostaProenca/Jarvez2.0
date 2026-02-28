"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Role = void 0;
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
const AddFixedModifierToLifePoints_1 = require("../Action/AddFixedModifierToLifePoints");
const AddPerLevelModifierToLifePoints_1 = require("../Action/AddPerLevelModifierToLifePoints");
const AddPerLevelModifierToManaPoints_1 = require("../Action/AddPerLevelModifierToManaPoints");
const AddProficiency_1 = require("../Action/AddProficiency");
const ApplyRoleAbility_1 = require("../Action/ApplyRoleAbility");
const TrainSkill_1 = require("../Action/TrainSkill");
const FixedModifier_1 = require("../Modifier/FixedModifier/FixedModifier");
const PerLevelModifier_1 = require("../Modifier/PerLevelModifier/PerLevelModifier");
const Level_1 = require("../Sheet/Level");
class Role {
    static serializeBasic(role) {
        return {
            abilities: Object.values(role.abilitiesPerLevel)
                .flatMap(levelAbilities => Object.values(levelAbilities)
                .map(roleAbility => roleAbility.serialize())),
            initialLifePoints: role.initialLifePoints,
            lifePointsPerLevel: role.lifePointsPerLevel,
            manaPerLevel: role.manaPerLevel,
            mandatorySkills: role.mandatorySkills,
            proficiencies: role.proficiencies,
            selectSkillGroups: role.selectSkillGroups,
            startsWithArmor: role.startsWithArmor,
            totalInitialSkills: role.getTotalInitialSkills(),
            name: role.name,
            chosenSkills: role.chosenSkills,
            selectedSkillsByGroup: role.selectedSkillsByGroup,
        };
    }
    get startsWithArmor() {
        return true;
    }
    get chosenSkills() {
        return this.selectedSkillsByGroup.flat();
    }
    /**
 * Returns an instance of this role.
 * @param chosenSkills - Chosen role skills to be trained
  **/
    constructor(selectedSkillsByGroup, selectSkillGroups) {
        this.selectedSkillsByGroup = selectedSkillsByGroup;
        this.selectSkillGroups = selectSkillGroups;
        this.validateChosenSkills();
    }
    addToSheet(transaction) {
        this.addLifePointsModifiers(transaction);
        this.addManaPointsModifiers(transaction);
        this.trainSkills(transaction);
        this.addProficiencies(transaction);
        this.addLevelOneAbilities(transaction);
    }
    addLevelOneAbilities(transaction) {
        const abilities = this.abilitiesPerLevel[Level_1.Level.one];
        Object.values(abilities).forEach(ability => {
            transaction.run(new ApplyRoleAbility_1.ApplyRoleAbility({
                payload: {
                    ability,
                    source: this.name,
                },
                transaction,
            }));
        });
    }
    getTotalInitialSkills() {
        return this.mandatorySkills.length + this.selectSkillGroups.reduce((acc, curr) => curr.amount + acc, 0);
    }
    serialize() {
        return Object.assign(Object.assign({}, Role.serializeBasic(this)), this.serializeSpecific());
    }
    addLifePointsModifiers(transaction) {
        transaction.run(new AddFixedModifierToLifePoints_1.AddFixedModifierToLifePoints({
            payload: {
                modifier: new FixedModifier_1.FixedModifier(this.name, this.initialLifePoints, new Set(['constitution'])),
            },
            transaction,
        }));
        transaction.run(new AddPerLevelModifierToLifePoints_1.AddPerLevelModifierToLifePoints({
            payload: {
                modifier: new PerLevelModifier_1.PerLevelModifier({
                    source: this.name,
                    value: this.lifePointsPerLevel,
                    includeFirstLevel: false,
                    attributeBonuses: new Set(['constitution']),
                }),
            },
            transaction,
        }));
    }
    addManaPointsModifiers(transaction) {
        transaction.run(new AddPerLevelModifierToManaPoints_1.AddPerLevelModifierToManaPoints({
            payload: {
                modifier: new PerLevelModifier_1.PerLevelModifier({
                    source: this.name,
                    value: this.manaPerLevel,
                    includeFirstLevel: true,
                }),
            },
            transaction,
        }));
    }
    addProficiencies(transaction) {
        this.proficiencies.forEach(proficiency => {
            transaction.run(new AddProficiency_1.AddProficiency({
                payload: {
                    proficiency,
                    source: this.name,
                },
                transaction,
            }));
        });
    }
    trainSkills(transaction) {
        this.mandatorySkills.forEach(skill => {
            transaction.run(new TrainSkill_1.TrainSkill({
                payload: {
                    skill,
                    source: this.name,
                },
                transaction,
            }));
        });
        this.chosenSkills.forEach(skill => {
            transaction.run(new TrainSkill_1.TrainSkill({
                payload: {
                    skill,
                    source: this.name,
                },
                transaction,
            }));
        });
    }
    validateChosenSkills() {
        const isSomeRepeated = this.chosenSkills.some((skill, index) => this.chosenSkills.indexOf(skill) !== index);
        if (isSomeRepeated) {
            throw new SheetBuilderError_1.SheetBuilderError('REPEATED_ROLE_SKILLS');
        }
        const chosenSkills = this.chosenSkills.slice();
        const groupCounters = [];
        this.selectSkillGroups.forEach(group => {
            let groupCounter = group.amount;
            for (let index = 0; index <= group.skills.length; index += 1) {
                const groupSkill = group.skills[index];
                const foundIndex = chosenSkills.findIndex(chosen => chosen === groupSkill);
                if (foundIndex >= 0) {
                    groupCounter -= 1;
                    chosenSkills.splice(foundIndex, 1);
                    if (groupCounter === 0) {
                        break;
                    }
                }
            }
            groupCounters.push(groupCounter);
        });
        if (chosenSkills.length) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_CHOSEN_SKILLS');
        }
        if (groupCounters.some(counter => counter !== 0)) {
            throw new SheetBuilderError_1.SheetBuilderError('MISSING_ROLE_SKILLS');
        }
    }
}
exports.Role = Role;
Role.startsWithArmor = true;
