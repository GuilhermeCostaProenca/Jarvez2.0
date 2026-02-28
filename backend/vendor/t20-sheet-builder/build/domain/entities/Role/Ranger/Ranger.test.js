"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Ranger_1 = require("./Ranger");
describe('Ranger', () => {
    let ranger;
    let sheet;
    let transaction;
    beforeEach(() => {
        const chosenSkills = [
            [Skill_1.SkillName.fight],
            [
                Skill_1.SkillName.animalHandling,
                Skill_1.SkillName.athletics,
                Skill_1.SkillName.animalRide,
                Skill_1.SkillName.cure,
                Skill_1.SkillName.fortitude,
                Skill_1.SkillName.stealth,
            ],
        ];
        ranger = new Ranger_1.Ranger(chosenSkills);
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        ranger.addToSheet(transaction);
    });
    it('should have prey mark ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.preyMark)).toBeDefined();
    });
    it('should have tracker ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.tracker)).toBeDefined();
    });
    it('should have tracker +2 survival', () => {
        const survival = sheet.getSkill(Skill_1.SkillName.survival);
        expect(survival.getFixedModifier(RoleAbilityName_1.RoleAbilityName.tracker)).toBeDefined();
    });
    it('should have prey mark activateble effect', () => {
        const preyMark = sheet.getActivateableEffect(RoleAbilityName_1.RoleAbilityName.preyMark);
        expect(preyMark).toBeDefined();
        expect(preyMark === null || preyMark === void 0 ? void 0 : preyMark.executionType).toBe('moviment');
        expect(preyMark === null || preyMark === void 0 ? void 0 : preyMark.getManaCost()).toBe(1);
    });
});
