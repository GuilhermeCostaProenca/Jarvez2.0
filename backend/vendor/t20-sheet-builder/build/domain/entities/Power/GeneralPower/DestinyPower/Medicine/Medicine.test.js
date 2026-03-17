"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../../../Sheet");
const Transaction_1 = require("../../../../Sheet/Transaction");
const Skill_1 = require("../../../../Skill");
const Medicine_1 = require("./Medicine");
describe('Medicine', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should require wisdom 1', () => {
        const medicine = new Medicine_1.Medicine();
        transaction.sheet.getSheetSkills().trainSkill(Skill_1.SkillName.cure);
        expect(() => {
            medicine.addToSheet(transaction);
            medicine.verifyRequirements(transaction.sheet);
        }).toThrow('Requisito não preenchido: Sabedoria +1');
    });
    it('should require cure training', () => {
        const medicine = new Medicine_1.Medicine();
        transaction.sheet.getSheetAttributes().getValues().wisdom = 1;
        expect(() => {
            medicine.addToSheet(transaction);
            medicine.verifyRequirements(transaction.sheet);
        }).toThrow('Requisito não preenchido: Treinado em Cura');
    });
});
