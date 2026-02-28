"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const __1 = require("../..");
const ResistanceName_1 = require("../../Resistance/ResistanceName");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const RaceAbilityName_1 = require("../RaceAbilityName");
const RaceName_1 = require("../RaceName");
const Lefeu_1 = require("./Lefeu");
describe('Lefeu', () => {
    it('should apply +1 to strength, dexterity and constitution, and -1 to charisma', () => {
        const lefeu = new Lefeu_1.Lefeu(['strength', 'constitution', 'dexterity']);
        lefeu.addDeformities([SkillName_1.SkillName.acrobatics, SkillName_1.SkillName.animalHandling]);
        const sheet = new __1.BuildingSheet();
        const transaction = new Transaction_1.Transaction(sheet);
        lefeu.addToSheet(transaction);
        expect(sheet.getSheetAttributes().getValues().charisma).toBe(-1);
        expect(sheet.getSheetAttributes().getValues().strength).toBe(1);
        expect(sheet.getSheetAttributes().getValues().constitution).toBe(1);
        expect(sheet.getSheetAttributes().getValues().dexterity).toBe(1);
    });
    it('should have a previous race default human', () => {
        const lefeu = new Lefeu_1.Lefeu(['strength', 'constitution', 'dexterity']);
        expect(lefeu.getPreviousRace()).toBe(RaceName_1.RaceName.human);
    });
    it('should be able to change previous race', () => {
        const lefeu = new Lefeu_1.Lefeu(['strength', 'constitution', 'dexterity']);
        lefeu.setPreviousRace(RaceName_1.RaceName.elf);
        expect(lefeu.getPreviousRace()).toBe(RaceName_1.RaceName.elf);
    });
    it('should throw error when selecting charisma', () => {
        expect(() => {
            const lefeu = new Lefeu_1.Lefeu([
                'dexterity',
                'strength',
                'charisma',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should throw error with more than 3 selections', () => {
        expect(() => {
            const lefeu = new Lefeu_1.Lefeu([
                'constitution',
                'dexterity',
                'strength',
                'charisma',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should throw error with less than 3 selections', () => {
        expect(() => {
            const lefeu = new Lefeu_1.Lefeu([
                'constitution',
                'strength',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should throw error with repeated attributes', () => {
        expect(() => {
            const lefeu = new Lefeu_1.Lefeu([
                'constitution',
                'dexterity',
                'dexterity',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should add skills with deformities', () => {
        const lefeu = new Lefeu_1.Lefeu([
            'constitution',
            'dexterity',
            'strength',
        ]);
        lefeu.addDeformities([SkillName_1.SkillName.acrobatics, SkillName_1.SkillName.animalHandling]);
        const sheet = new __1.BuildingSheet();
        const transaction = new Transaction_1.Transaction(sheet);
        lefeu.addToSheet(transaction);
        const { acrobatics, animalHandling } = sheet.getSheetSkills().getSkills();
        const acrobaticsModifier = acrobatics.fixedModifiers.modifiers[0];
        const animalHandlingModifier = animalHandling.fixedModifiers.modifiers[0];
        expect(acrobaticsModifier.baseValue).toBe(2);
        expect(animalHandlingModifier.baseValue).toBe(2);
        expect(acrobaticsModifier.source).toBe(RaceAbilityName_1.RaceAbilityName.deformity);
        expect(animalHandlingModifier.source).toBe(RaceAbilityName_1.RaceAbilityName.deformity);
    });
    it('should throw error if try to select more then 2 deformities', () => {
        expect(() => {
            const lefeu = new Lefeu_1.Lefeu([
                'constitution',
                'dexterity',
                'strength',
            ]);
            lefeu.addDeformities([SkillName_1.SkillName.acrobatics, SkillName_1.SkillName.animalRide, SkillName_1.SkillName.diplomacy]);
        }).toThrow('EXCEEDED_CHOICES_QUANTITY');
    });
    it('should throw error if select repeated deformitis', () => {
        expect(() => {
            const lefeu = new Lefeu_1.Lefeu([
                'constitution',
                'dexterity',
                'strength',
            ]);
            lefeu.addDeformities([SkillName_1.SkillName.acrobatics, SkillName_1.SkillName.acrobatics]);
        }).toThrow('REPEATED_DEFORMITY_CHOICE');
    });
    it('should add resistances', () => {
        const lefeu = new Lefeu_1.Lefeu([
            'constitution',
            'dexterity',
            'strength',
        ]);
        lefeu.addDeformities([SkillName_1.SkillName.acrobatics, SkillName_1.SkillName.animalRide]);
        const sheet = new __1.BuildingSheet();
        const transaction = new Transaction_1.Transaction(sheet);
        lefeu.addToSheet(transaction);
        const attributes = sheet.getSheetAttributes().getValues();
        expect(sheet.getSheetResistences().getTotal(ResistanceName_1.ResistanceName.lefeu, attributes)).toBe(5);
        expect(sheet.getSheetResistences().getTotal(ResistanceName_1.ResistanceName.tormenta, attributes)).toBe(5);
    });
});
