"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Power_1 = require("../../../Power");
const Dodge_1 = require("../../../Power/GeneralPower/CombatPower/Dodge/Dodge");
const GeneralPowerName_1 = require("../../../Power/GeneralPower/GeneralPowerName");
const Sheet_1 = require("../../../Sheet");
const Transaction_1 = require("../../../Sheet/Transaction");
const SkillName_1 = require("../../../Skill/SkillName");
const Versatile_1 = require("./Versatile");
const VersatileChoicePower_1 = require("./VersatileChoicePower");
const VersatileChoiceSkill_1 = require("./VersatileChoiceSkill");
describe('Versatile', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should add choice', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        expect(versatile.effects.passive.default.choices).toEqual([new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics)]);
    });
    it('should not add repeated choice', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        expect(() => {
            versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        }).toThrowError('REPEATED_VERSATILE_CHOICE');
    });
    it('should not allow more than two choices', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.animalHandling));
        expect(() => {
            versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.fight));
        }).toThrow('EXCEEDED_CHOICES_QUANTITY');
    });
    it('should not allow 2 powers', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoicePower_1.VersatileChoicePower(new Dodge_1.Dodge()));
        expect(() => {
            versatile.addChoice(new VersatileChoicePower_1.VersatileChoicePower(new Power_1.OneWeaponStyle()));
        }).toThrow('FORBIDDEN_TWO_POWERS');
    });
    it('should allow 1 power and 1 skill', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        versatile.addChoice(new VersatileChoicePower_1.VersatileChoicePower(new Power_1.OneWeaponStyle()));
        expect(versatile.effects.passive.default.choices[0].name).toEqual(SkillName_1.SkillName.acrobatics);
        expect(versatile.effects.passive.default.choices[1].name).toEqual(GeneralPowerName_1.GeneralPowerName.oneWeaponStyle);
    });
    it('should not allow apply without choices', () => {
        const versatile = new Versatile_1.Versatile();
        expect(() => {
            versatile.addToSheet(transaction);
        }).toThrow('MISSING_CHOICES');
    });
    it('should train chosen skills', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.animalHandling));
        versatile.addToSheet(transaction);
        const firstChoice = sheet.getSkills()[SkillName_1.SkillName.acrobatics];
        const secondChoice = sheet.getSkills()[SkillName_1.SkillName.animalHandling];
        expect(firstChoice.skill.getIsTrained()).toBe(true);
        expect(secondChoice.skill.getIsTrained()).toBe(true);
    });
    it('should apply chosen power', () => {
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
        versatile.addChoice(new VersatileChoicePower_1.VersatileChoicePower(new Dodge_1.Dodge()));
        transaction.sheet.getSheetAttributes().getValues().dexterity = 1;
        versatile.addToSheet(transaction);
        const firstChoice = sheet.getSkills()[SkillName_1.SkillName.acrobatics];
        const secondChoice = sheet.getSheetPowers().getGeneralPowers().get(GeneralPowerName_1.GeneralPowerName.dodge);
        expect(firstChoice.skill.getIsTrained()).toBe(true);
        expect(secondChoice).toBeDefined();
    });
});
