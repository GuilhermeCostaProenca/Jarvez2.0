"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const InGameContextFake_1 = require("../../../Context/InGameContextFake");
const Sheet_1 = require("../../../Sheet");
const Transaction_1 = require("../../../Sheet/Transaction");
const Vision_1 = require("../../../Sheet/Vision");
const SkillName_1 = require("../../../Skill/SkillName");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const RockKnowledge_1 = require("./RockKnowledge");
describe('RockKnowledge', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should provide dark vision', () => {
        const rockKnowledge = new RockKnowledge_1.RockKnowledge();
        rockKnowledge.addToSheet(transaction);
        expect(sheet.getSheetVision().getVision()).toBe(Vision_1.Vision.dark);
    });
    it('should dispatch +2 perception bonus', () => {
        const rockKnowledge = new RockKnowledge_1.RockKnowledge();
        rockKnowledge.addToSheet(transaction);
        const perceptionModifier = sheet.getSkills()[SkillName_1.SkillName.perception].skill.contextualModifiers.get(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        expect(perceptionModifier).toBeDefined();
        expect(perceptionModifier === null || perceptionModifier === void 0 ? void 0 : perceptionModifier.baseValue).toBe(2);
    });
    it('should dispatch +2 survival bonus', () => {
        const rockKnowledge = new RockKnowledge_1.RockKnowledge();
        rockKnowledge.addToSheet(transaction);
        const survivalModifier = sheet.getSkills()[SkillName_1.SkillName.survival].skill.contextualModifiers.get(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        expect(survivalModifier).toBeDefined();
        expect(survivalModifier === null || survivalModifier === void 0 ? void 0 : survivalModifier.baseValue).toBe(2);
    });
    it('should not activate bonus in game context outside underground', () => {
        const rockKnowledge = new RockKnowledge_1.RockKnowledge();
        rockKnowledge.addToSheet(transaction);
        const perceptionModifier = sheet.getSkills()[SkillName_1.SkillName.perception].skill.contextualModifiers.get(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        const survivalModifier = sheet.getSkills()[SkillName_1.SkillName.survival].skill.contextualModifiers.get(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        const context = new InGameContextFake_1.InGameContextFake();
        context.location.isUnderground = false;
        expect(survivalModifier === null || survivalModifier === void 0 ? void 0 : survivalModifier.condition.verify(context)).toBe(false);
        expect(perceptionModifier === null || perceptionModifier === void 0 ? void 0 : perceptionModifier.condition.verify(context)).toBe(false);
    });
    it('should activate bonus in game context inside underground', () => {
        const rockKnowledge = new RockKnowledge_1.RockKnowledge();
        rockKnowledge.addToSheet(transaction);
        const perceptionModifier = sheet.getSkills()[SkillName_1.SkillName.perception].skill.contextualModifiers.get(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        const survivalModifier = sheet.getSkills()[SkillName_1.SkillName.survival].skill.contextualModifiers.get(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        const context = new InGameContextFake_1.InGameContextFake();
        context.location.isUnderground = true;
        expect(survivalModifier === null || survivalModifier === void 0 ? void 0 : survivalModifier.condition.verify(context)).toBe(true);
        expect(perceptionModifier === null || perceptionModifier === void 0 ? void 0 : perceptionModifier.condition.verify(context)).toBe(true);
    });
});
