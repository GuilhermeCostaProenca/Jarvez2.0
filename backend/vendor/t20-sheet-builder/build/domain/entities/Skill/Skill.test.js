"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const InGameContextFake_1 = require("../Context/InGameContextFake");
const OutOfGameContext_1 = require("../Context/OutOfGameContext");
const ContextualModifier_1 = require("../Modifier/ContextualModifier/ContextualModifier");
const FixedModifier_1 = require("../Modifier/FixedModifier/FixedModifier");
const RaceAbilityName_1 = require("../Race/RaceAbilityName");
const BuildingSheetFake_1 = require("../Sheet/BuildingSheet/BuildingSheetFake");
const Skill_1 = require("./Skill");
const SkillName_1 = require("./SkillName");
const SkillTotalCalculatorFactory_1 = require("./SkillTotalCalculatorFactory");
describe('Skill', () => {
    let sheet;
    beforeEach(() => {
        sheet = new BuildingSheetFake_1.BuildingSheetFake();
    });
    it('should calculate level 1 untrained skill', () => {
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            attribute: 'dexterity',
        });
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(0);
    });
    it('should update total by training', () => {
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            attribute: 'dexterity',
        });
        skill.train();
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(2);
    });
    it('should calculate level 1 untrained skill with modifier', () => {
        sheet.getSheetAttributes().getValues().dexterity = 2;
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            attribute: 'dexterity',
        });
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(2);
    });
    it('should calculate level 1 trained skill', () => {
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            isTrained: true,
            attribute: 'dexterity',
        });
        const sheetAttributes = sheet.getSheetAttributes().getValues();
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheetAttributes, sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(2);
    });
    it('should calculate level 1 trained skill with attribute modifier', () => {
        sheet.getSheetAttributes().getValues().dexterity = 2;
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            isTrained: true,
            attribute: 'dexterity',
        });
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(4);
    });
    it('should calculate level 1 trained skill with attribute modifier and fixed modifier', () => {
        sheet.getSheetAttributes().getValues().dexterity = 2;
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            isTrained: true,
            attribute: 'dexterity',
        });
        skill.fixedModifiers.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.versatile, 2));
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(6);
    });
    it('should calculate level 10 trained skill with attribute modifier and fixed modifier', () => {
        sheet.getSheetAttributes().getValues().dexterity = 2;
        sheet.setLevel(10);
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            isTrained: true,
            attribute: 'dexterity',
        });
        skill.fixedModifiers.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.versatile, 2));
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(13);
    });
    it('should calculate level 10 trained skill with attribute modifier, fixed modifier and contextual modifier using out of game context', () => {
        sheet.getSheetAttributes().getValues().dexterity = 2;
        sheet.setLevel(10);
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            isTrained: true,
            attribute: 'dexterity',
        });
        skill.fixedModifiers.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.versatile, 2));
        skill.contextualModifiers.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.rockKnowledge,
            value: 5,
            condition: { description: 'any', verify: context => { var _a, _b; return (_b = (_a = context.getCurrentLocation()) === null || _a === void 0 ? void 0 : _a.isUnderground) !== null && _b !== void 0 ? _b : false; } },
        }));
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new OutOfGameContext_1.OutOfGameContext());
        expect(skill.getTotal(calculator)).toBe(13);
    });
    it('should calculate level 10 trained skill with attribute modifier, fixed modifier and contextual modifier using in game context', () => {
        sheet.getSheetAttributes().getValues().dexterity = 2;
        sheet.setLevel(10);
        const skill = new Skill_1.Skill({
            name: SkillName_1.SkillName.acrobatics,
            isTrained: true,
            attribute: 'dexterity',
        });
        skill.fixedModifiers.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.versatile, 2));
        skill.contextualModifiers.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.rockKnowledge,
            value: 5,
            condition: {
                description: 'any', verify: context => { var _a, _b; return (_b = (_a = context.getCurrentLocation()) === null || _a === void 0 ? void 0 : _a.isUnderground) !== null && _b !== void 0 ? _b : false; },
            },
        }));
        const calculator = SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(sheet.getSheetAttributes().getValues(), sheet.getLevel(), new InGameContextFake_1.InGameContextFake());
        expect(skill.getTotal(calculator)).toBe(18);
    });
});
