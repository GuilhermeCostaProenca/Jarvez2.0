"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../../Sheet");
const Transaction_1 = require("../../../Sheet/Transaction");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const HardAsRock_1 = require("./HardAsRock");
describe('HardAsRock', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch addOtherModifierToLifePoints', () => {
        const hardAsRock = new HardAsRock_1.HardAsRock();
        hardAsRock.addToSheet(transaction);
        const lifePointsModifier = sheet.getSheetLifePoints().getFixedModifiers().get(RaceAbilityName_1.RaceAbilityName.hardAsRock);
        expect(lifePointsModifier).toBeDefined();
        expect(lifePointsModifier === null || lifePointsModifier === void 0 ? void 0 : lifePointsModifier.baseValue).toBe(3);
    });
    it('should dispatch addPerLevelModifierToLifePoints', () => {
        const hardAsRock = new HardAsRock_1.HardAsRock();
        hardAsRock.addToSheet(transaction);
        const lifePointsModifier = sheet.getSheetLifePoints().getPerLevelModifiers().get(RaceAbilityName_1.RaceAbilityName.hardAsRock);
        expect(lifePointsModifier).toBeDefined();
        expect(lifePointsModifier === null || lifePointsModifier === void 0 ? void 0 : lifePointsModifier.baseValue).toBe(1);
        expect(lifePointsModifier === null || lifePointsModifier === void 0 ? void 0 : lifePointsModifier.includeFirstLevel).toBe(false);
    });
});
