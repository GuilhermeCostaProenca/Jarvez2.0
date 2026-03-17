"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const Modifier_1 = require("../../Modifier");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Elf_1 = require("./Elf");
const RaceAbilityName_1 = require("../RaceAbilityName");
(0, vitest_1.describe)('Elf', () => {
    let sheet;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        const elf = new Elf_1.Elf();
        const builder = new SheetBuilder_1.SheetBuilder(sheet);
        builder.chooseRace(elf);
    });
    (0, vitest_1.it)('should apply +2 to intelligence, +1 to dexterity and -1 to constitution', () => {
        const attributes = sheet.getSheetAttributes().getValues();
        (0, vitest_1.expect)(attributes.strength).toBe(0);
        (0, vitest_1.expect)(attributes.dexterity).toBe(1);
        (0, vitest_1.expect)(attributes.constitution).toBe(-1);
        (0, vitest_1.expect)(attributes.intelligence).toBe(2);
        (0, vitest_1.expect)(attributes.wisdom).toBe(0);
        (0, vitest_1.expect)(attributes.charisma).toBe(0);
    });
    (0, vitest_1.it)('should change default displacement to 12m', () => {
        (0, vitest_1.expect)(sheet.getSheetDisplacement().getDisplacement()).toEqual(12);
    });
    (0, vitest_1.it)('should add +1 mana points per level modifier', () => {
        const modifiers = sheet.getSheetManaPoints().getPerLevelModifiers();
        (0, vitest_1.expect)(modifiers.modifiers).toHaveLength(1);
        (0, vitest_1.expect)(modifiers.modifiers[0].baseValue).toBe(1);
        (0, vitest_1.expect)(modifiers.modifiers[0].source).toBe(RaceAbilityName_1.RaceAbilityName.magicBlood);
        (0, vitest_1.expect)(modifiers.getTotal(new Modifier_1.PerLevelModifiersListTotalCalculator(sheet.getSheetAttributes().getValues(), Sheet_1.Level.one))).toBe(1);
    });
    (0, vitest_1.it)('should have penumbra vision', () => {
        const vision = sheet.getSheetVision().getVision();
        (0, vitest_1.expect)(vision).toBe(Sheet_1.Vision.penumbra);
    });
    (0, vitest_1.it)('should add +2 to mysticism and perception', () => {
        const skills = sheet.getSheetSkills().getSkills();
        const mysticismModifier = skills.mysticism.fixedModifiers.modifiers[0];
        const perceptionModifier = skills.perception.fixedModifiers.modifiers[0];
        (0, vitest_1.expect)(mysticismModifier.baseValue).toBe(2);
        (0, vitest_1.expect)(mysticismModifier.source).toBe(RaceAbilityName_1.RaceAbilityName.elvenSenses);
        (0, vitest_1.expect)(perceptionModifier.baseValue).toBe(2);
        (0, vitest_1.expect)(perceptionModifier.source).toBe(RaceAbilityName_1.RaceAbilityName.elvenSenses);
    });
});
