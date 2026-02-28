"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Power_1 = require("../../Power");
const Dodge_1 = require("../../Power/GeneralPower/CombatPower/Dodge/Dodge");
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const Human_1 = require("./Human");
const Versatile_1 = require("./Versatile/Versatile");
const VersatileChoicePower_1 = require("./Versatile/VersatileChoicePower");
const VersatileChoiceSkill_1 = require("./Versatile/VersatileChoiceSkill");
describe('Human', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should apply +1 to strength, dexterity and constitution', () => {
        const acrobatics = new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics);
        const animalHandling = new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.animalHandling);
        const human = new Human_1.Human([
            'constitution',
            'dexterity',
            'strength',
        ]);
        human.addVersatilChoice(acrobatics);
        human.addVersatilChoice(animalHandling);
        human.addToSheet(transaction);
        expect(sheet.getSheetAttributes().getValues()).toEqual({
            strength: 1,
            dexterity: 1,
            constitution: 1,
            intelligence: 0,
            wisdom: 0,
            charisma: 0,
        });
    });
    it('should throw error with more than 3 selections', () => {
        expect(() => {
            const human = new Human_1.Human([
                'constitution',
                'dexterity',
                'strength',
                'charisma',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should throw error with less than 3 selections', () => {
        expect(() => {
            const human = new Human_1.Human([
                'constitution',
                'charisma',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should throw error with repeated attributes', () => {
        expect(() => {
            const human = new Human_1.Human([
                'constitution',
                'charisma',
                'charisma',
            ]);
        }).toThrow('INVALID_ATTRIBUTES_SELECTION');
    });
    it('should add skills with versatile', () => {
        const human = new Human_1.Human([
            'constitution',
            'dexterity',
            'strength',
        ], [
            new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics),
        ]);
        expect(human.versatileChoices).toContainEqual(new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics));
    });
    it('should apply versatile with chosen skills', () => {
        const acrobatics = new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics);
        const animalHandling = new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.animalHandling);
        const human = new Human_1.Human([
            'constitution',
            'dexterity',
            'strength',
        ], [
            acrobatics,
            animalHandling,
        ]);
        human.addToSheet(transaction);
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(acrobatics);
        versatile.addChoice(animalHandling);
        const skills = sheet.getSkills();
        expect(skills[SkillName_1.SkillName.acrobatics].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.animalHandling].skill.getIsTrained()).toBe(true);
    });
    it('should apply versatile training chosen skill and power', () => {
        const acrobatics = new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics);
        const dodge = new VersatileChoicePower_1.VersatileChoicePower(new Dodge_1.Dodge());
        const human = new Human_1.Human([
            'constitution',
            'dexterity',
            'strength',
        ], [acrobatics, dodge]);
        transaction.sheet.getSheetAttributes().getValues().dexterity = 1;
        human.addToSheet(transaction);
        const versatile = new Versatile_1.Versatile();
        versatile.addChoice(acrobatics);
        versatile.addChoice(dodge);
        const skills = sheet.getSkills();
        const powers = sheet.getSheetPowers().getGeneralPowers();
        expect(skills[SkillName_1.SkillName.acrobatics].skill.getIsTrained()).toBe(true);
        expect(powers.get(Power_1.GeneralPowerName.dodge)).toBeDefined();
    });
});
