"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Goblin_1 = require("./Goblin");
const RaceAbilityName_1 = require("../RaceAbilityName");
(0, vitest_1.describe)('Elf', () => {
    let sheet;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        const goblin = new Goblin_1.Goblin();
        const builder = new SheetBuilder_1.SheetBuilder(sheet);
        builder.chooseRace(goblin);
    });
    (0, vitest_1.it)('should apply +2 to dexterity, +1 to intelligence and -1 to charisma', () => {
        const attributes = sheet.getSheetAttributes().getValues();
        (0, vitest_1.expect)(attributes.strength).toBe(0);
        (0, vitest_1.expect)(attributes.dexterity).toBe(2);
        (0, vitest_1.expect)(attributes.constitution).toBe(0);
        (0, vitest_1.expect)(attributes.intelligence).toBe(1);
        (0, vitest_1.expect)(attributes.wisdom).toBe(0);
        (0, vitest_1.expect)(attributes.charisma).toBe(-1);
    });
    (0, vitest_1.it)('should have ingenious ability', () => {
        const abilities = sheet.getSheetAbilities().getRaceAbilities();
        (0, vitest_1.expect)(abilities.has(RaceAbilityName_1.RaceAbilityName.ingenious)).toBe(true);
    });
    (0, vitest_1.it)('should have dark vision', () => {
        const vision = sheet.getSheetVision().getVision();
        (0, vitest_1.expect)(vision).toBe(Sheet_1.Vision.dark);
    });
    (0, vitest_1.it)('should have climbing displacement equal to terrestrial displacement', () => {
        const displacement = sheet.getSheetDisplacement().getDisplacement();
        const climbingDisplacement = sheet.getSheetDisplacement().getClimbingDisplacement();
        (0, vitest_1.expect)(climbingDisplacement).toBe(displacement);
    });
    (0, vitest_1.it)('should have small size', () => {
        const size = sheet.getSheetSize().getSize();
        (0, vitest_1.expect)(size).toBe('small');
    });
    (0, vitest_1.it)('should have 9m displacement', () => {
        const displacement = sheet.getSheetDisplacement().getDisplacement();
        (0, vitest_1.expect)(displacement).toBe(9);
    });
    (0, vitest_1.it)('should add +2 modifier to fortitude', () => {
        const { fortitude } = sheet.getSheetSkills().getSkills();
        const modifier = fortitude.fixedModifiers.modifiers[0];
        (0, vitest_1.expect)(modifier.baseValue).toBe(2);
        (0, vitest_1.expect)(modifier.source).toBe(RaceAbilityName_1.RaceAbilityName.streetRat);
    });
});
