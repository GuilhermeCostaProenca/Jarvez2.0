"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Barbarian_1 = require("./Barbarian");
describe('Barbarian', () => {
    let sheet;
    let transaction;
    let barbarian;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        barbarian = new Barbarian_1.Barbarian([[
                Skill_1.SkillName.animalHandling,
                Skill_1.SkillName.athletics,
                Skill_1.SkillName.animalRide,
                Skill_1.SkillName.initiative,
            ]]);
        barbarian.addToSheet(transaction);
    });
    it('should be have fortitude and fight trained', () => {
        const skills = sheet.getSkills();
        expect(skills[Skill_1.SkillName.fortitude].skill.getIsTrained()).toBe(true);
        expect(skills[Skill_1.SkillName.fight].skill.getIsTrained()).toBe(true);
    });
    it('should dispatch profiencies add', () => {
        const proficiencies = transaction.sheet.getSheetProficiencies().getProficiencies();
        expect(proficiencies).toContain(Sheet_1.Proficiency.martial);
        expect(proficiencies).toContain(Sheet_1.Proficiency.shield);
    });
    it('should dispatch life points fixed modifier add', () => {
        const lifePoints = sheet.getSheetLifePoints();
        const fixedModifier = lifePoints.getFixedModifiers().get(RoleName_1.RoleName.barbarian);
        expect(fixedModifier).toBeDefined();
        expect(fixedModifier === null || fixedModifier === void 0 ? void 0 : fixedModifier.baseValue).toBe(24);
    });
    it('should dispatch life points per level modifier add', () => {
        const lifePoints = sheet.getSheetLifePoints();
        const perLevelModifier = lifePoints.getPerLevelModifiers().get(RoleName_1.RoleName.barbarian);
        expect(perLevelModifier).toBeDefined();
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.baseValue).toBe(6);
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.includeFirstLevel).toBe(false);
    });
    it('should dispatch mana points modifiers add', () => {
        const manaPoints = sheet.getSheetManaPoints();
        const perLevelModifier = manaPoints.getPerLevelModifiers().get(RoleName_1.RoleName.barbarian);
        expect(perLevelModifier).toBeDefined();
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.baseValue).toBe(3);
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.includeFirstLevel).toBe(true);
    });
    it('should dispatch rage ability add', () => {
        const abilities = sheet.getSheetAbilities();
        expect(abilities.getRoleAbilities().get(RoleAbilityName_1.RoleAbilityName.rage)).toBeDefined();
    });
});
