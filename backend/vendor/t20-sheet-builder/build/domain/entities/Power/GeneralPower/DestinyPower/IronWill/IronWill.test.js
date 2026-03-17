"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const BuildingSheet_1 = require("../../../../Sheet/BuildingSheet/BuildingSheet");
const Transaction_1 = require("../../../../Sheet/Transaction");
const SkillName_1 = require("../../../../Skill/SkillName");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const IronWill_1 = require("./IronWill");
describe('IronWill', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new BuildingSheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should require wisdom 1', () => {
        const ironWill = new IronWill_1.IronWill();
        expect(() => {
            ironWill.addToSheet(transaction);
            ironWill.verifyRequirements(transaction.sheet);
        }).toThrow('Requisito não preenchido: Sabedoria +1');
    });
    it('should dispatch mana points modifier add', () => {
        const ironWill = new IronWill_1.IronWill();
        transaction.sheet.getSheetAttributes().getValues().wisdom = 1;
        ironWill.addToSheet(transaction);
        const manaModifier = sheet.getSheetManaPoints().getPerLevelModifiers().get(GeneralPowerName_1.GeneralPowerName.ironWill);
        expect(manaModifier).toBeDefined();
        expect(manaModifier === null || manaModifier === void 0 ? void 0 : manaModifier.baseValue).toBe(1);
        expect(manaModifier === null || manaModifier === void 0 ? void 0 : manaModifier.includeFirstLevel).toBe(true);
        expect(manaModifier === null || manaModifier === void 0 ? void 0 : manaModifier.frequency).toBe(2);
    });
    it('should dispatch will modifier add', () => {
        const ironWill = new IronWill_1.IronWill();
        transaction.sheet.getSheetAttributes().getValues().wisdom = 1;
        ironWill.addToSheet(transaction);
        const willModifier = sheet.getSkills()[SkillName_1.SkillName.will].skill.fixedModifiers.get(GeneralPowerName_1.GeneralPowerName.ironWill);
        expect(willModifier).toBeDefined();
        expect(willModifier === null || willModifier === void 0 ? void 0 : willModifier.baseValue).toBe(2);
    });
});
