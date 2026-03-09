"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Proficiency_1 = require("../../Sheet/Proficiency");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Warrior_1 = require("./Warrior");
describe('Warrior', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch proper train skills', () => {
        const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.aim]]);
        warrior.addToSheet(transaction);
        const skills = transaction.sheet.getSkills();
        expect(skills[SkillName_1.SkillName.fight].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.animalHandling].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.aim].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.fortitude].skill.getIsTrained()).toBe(true);
    });
    it('should not train skills choosing more than allowed from the same group', () => {
        expect(() => {
            const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.aim, SkillName_1.SkillName.athletics]]);
        }).toThrow('INVALID_CHOSEN_SKILLS');
    });
    it('should not train skills with less than required', () => {
        expect(() => {
            const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling]]);
        }).toThrow('MISSING_ROLE_SKILLS');
    });
    it('should not train skills with repeated skills', () => {
        expect(() => {
            const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.fight]]);
        }).toThrow('REPEATED_ROLE_SKILLS');
    });
    it('should dispatch profiencies add', () => {
        const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.aim]]);
        warrior.addToSheet(transaction);
        const proficiencies = transaction.sheet.getSheetProficiencies().getProficiencies();
        expect(proficiencies).toContain(Proficiency_1.Proficiency.martial);
        expect(proficiencies).toContain(Proficiency_1.Proficiency.heavyArmor);
        expect(proficiencies).toContain(Proficiency_1.Proficiency.shield);
    });
    it('should dispatch abilities add', () => {
        const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.aim]]);
        warrior.addToSheet(transaction);
        expect(sheet.getSheetAbilities().getRoleAbilities().get(RoleAbilityName_1.RoleAbilityName.specialAttack)).toBeDefined();
    });
    it('should dispatch life points modifiers add', () => {
        const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.aim]]);
        warrior.addToSheet(transaction);
        const lifePoints = sheet.getSheetLifePoints();
        const fixedModifier = lifePoints.getFixedModifiers().get(RoleName_1.RoleName.warrior);
        const perLevelModifier = lifePoints.getPerLevelModifiers().get(RoleName_1.RoleName.warrior);
        expect(fixedModifier).toBeDefined();
        expect(fixedModifier === null || fixedModifier === void 0 ? void 0 : fixedModifier.baseValue).toBe(20);
        expect(perLevelModifier).toBeDefined();
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.baseValue).toBe(5);
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.includeFirstLevel).toBe(false);
    });
    it('should dispatch mana points modifiers add', () => {
        const warrior = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.aim]]);
        warrior.addToSheet(transaction);
        const manaPoints = sheet.getSheetManaPoints();
        const perLevelModifier = manaPoints.getPerLevelModifiers().get(RoleName_1.RoleName.warrior);
        expect(perLevelModifier).toBeDefined();
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.baseValue).toBe(3);
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.includeFirstLevel).toBe(true);
    });
});
