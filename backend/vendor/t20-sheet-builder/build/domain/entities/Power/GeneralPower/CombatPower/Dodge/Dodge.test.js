"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const BuildingSheet_1 = require("../../../../Sheet/BuildingSheet/BuildingSheet");
const Transaction_1 = require("../../../../Sheet/Transaction");
const SkillName_1 = require("../../../../Skill/SkillName");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const Dodge_1 = require("./Dodge");
describe('Dodge', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new BuildingSheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch defense bonus', () => {
        const dodge = new Dodge_1.Dodge();
        transaction.sheet.getSheetAttributes().getValues().dexterity = 1;
        dodge.addToSheet(transaction);
        const defenseModifier = sheet.getSheetDefense().getDefense().fixedModifiers.get(GeneralPowerName_1.GeneralPowerName.dodge);
        expect(defenseModifier).toBeDefined();
        expect(defenseModifier === null || defenseModifier === void 0 ? void 0 : defenseModifier.baseValue).toBe(2);
    });
    it('should dispatch reflexes bonus', () => {
        const dodge = new Dodge_1.Dodge();
        transaction.sheet.getSheetAttributes().getValues().dexterity = 1;
        dodge.addToSheet(transaction);
        const skillModifier = sheet.getSkills()[SkillName_1.SkillName.reflexes].skill.fixedModifiers.get(GeneralPowerName_1.GeneralPowerName.dodge);
        expect(skillModifier).toBeDefined();
        expect(skillModifier === null || skillModifier === void 0 ? void 0 : skillModifier.baseValue).toBe(2);
    });
    it('should require dexterity +1', () => {
        const dodge = new Dodge_1.Dodge();
        expect(() => {
            dodge.addToSheet(transaction);
            dodge.verifyRequirements(transaction.sheet);
        }).toThrow('Requisito não preenchido: Destreza +1');
    });
});
