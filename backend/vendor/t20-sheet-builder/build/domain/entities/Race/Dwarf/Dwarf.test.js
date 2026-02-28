"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const RaceAbilityName_1 = require("../RaceAbilityName");
const Dwarf_1 = require("./Dwarf");
describe('Dwarf', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch dwarf attributes modifiers appliance', () => {
        const dwarf = new Dwarf_1.Dwarf();
        dwarf.addToSheet(transaction);
        expect(sheet.getSheetAttributes().getValues()).toEqual({
            strength: 0,
            dexterity: -1,
            constitution: 2,
            intelligence: 0,
            wisdom: 1,
            charisma: 0,
        });
    });
    it('should dispatch rock knowledge appliance', () => {
        const dwarf = new Dwarf_1.Dwarf();
        dwarf.addToSheet(transaction);
        expect(sheet.getSheetAbilities().getRaceAbilities().get(RaceAbilityName_1.RaceAbilityName.rockKnowledge)).toBeDefined();
    });
    it('should dispatch slow and always appliance', () => {
        const dwarf = new Dwarf_1.Dwarf();
        dwarf.addToSheet(transaction);
        expect(sheet.getSheetAbilities().getRaceAbilities().get(RaceAbilityName_1.RaceAbilityName.slowAndAlways)).toBeDefined();
    });
    it('should dispatch Hard as Rock appliance', () => {
        const dwarf = new Dwarf_1.Dwarf();
        dwarf.addToSheet(transaction);
        expect(sheet.getSheetAbilities().getRaceAbilities().get(RaceAbilityName_1.RaceAbilityName.hardAsRock)).toBeDefined();
    });
    it('should dispatch Heredrimm Tradition appliance', () => {
        const dwarf = new Dwarf_1.Dwarf();
        dwarf.addToSheet(transaction);
        expect(sheet.getSheetAbilities().getRaceAbilities().get(RaceAbilityName_1.RaceAbilityName.heredrimmTradition)).toBeDefined();
    });
});
