"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Minotaur_1 = require("./Minotaur");
const Inventory_1 = require("../../Inventory");
const DefenseTotalCalculatorFactory_1 = require("../../Defense/DefenseTotalCalculatorFactory");
(0, vitest_1.describe)('Minotaur', () => {
    let sheet;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        const minotaur = new Minotaur_1.Minotaur();
        const builder = new SheetBuilder_1.SheetBuilder(sheet);
        builder.chooseRace(minotaur);
    });
    (0, vitest_1.it)('should apply +2 to strength, +1 to constitution and -1 to wisdom', () => {
        const attributes = sheet.getSheetAttributes().getValues();
        (0, vitest_1.expect)(attributes.strength).toBe(2);
        (0, vitest_1.expect)(attributes.dexterity).toBe(0);
        (0, vitest_1.expect)(attributes.constitution).toBe(1);
        (0, vitest_1.expect)(attributes.intelligence).toBe(0);
        (0, vitest_1.expect)(attributes.wisdom).toBe(-1);
        (0, vitest_1.expect)(attributes.charisma).toBe(0);
    });
    (0, vitest_1.it)('should have hornes', () => {
        const attackName = Inventory_1.EquipmentName.horns;
        const inventory = sheet.getSheetInventory();
        (0, vitest_1.expect)(inventory.getEquipment(attackName)).to.not.equal(null);
    });
    (0, vitest_1.it)('should have +1 in defense', () => {
        const defense = sheet.getSheetDefense().getDefense();
        const attributes = sheet.getSheetAttributes().getValues();
        const calculator = DefenseTotalCalculatorFactory_1.DefenseTotalCalculatorFactory.make(attributes, 0, 0);
        (0, vitest_1.expect)(defense.getTotal(calculator)).toBe(11);
    });
});
