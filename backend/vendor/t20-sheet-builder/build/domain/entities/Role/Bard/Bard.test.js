"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const Spell_1 = require("../../Spell");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Bard_1 = require("./Bard");
describe('Bard', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        const chosenSkills = [[SkillName_1.SkillName.acrobatics, SkillName_1.SkillName.animalRide, SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy, SkillName_1.SkillName.cheat, SkillName_1.SkillName.stealth]];
        const chosenSchools = [Spell_1.SpellSchool.abjuration, Spell_1.SpellSchool.illusion, Spell_1.SpellSchool.divination];
        const chosenSpells = [new Spell_1.ArcaneArmor(), new Spell_1.IllusoryDisguise()];
        const bard = new Bard_1.Bard(chosenSkills, chosenSchools, chosenSpells);
        bard.addToSheet(transaction);
    });
    it('should have inspiration', () => {
        expect(sheet.getSheetAbilities().getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.inspiration)).toBeDefined();
    });
    it('should have bard spells', () => {
        expect(sheet.getSheetAbilities().getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.bardSpells)).toBeDefined();
    });
    it('should choose 3 spell schools', () => {
        const learnedSchools = sheet.getSheetSpells().getLearnedSchools();
        expect(learnedSchools.arcane).toHaveLength(3);
        expect(learnedSchools.arcane).toEqual(new Set([
            Spell_1.SpellSchool.abjuration,
            Spell_1.SpellSchool.illusion,
            Spell_1.SpellSchool.divination,
        ]));
    });
    it('should learn 2 spells', () => {
        const spells = sheet.getSheetSpells().getSpells();
        expect(spells).toHaveLength(2);
        expect(spells.get(Spell_1.SpellName.arcaneArmor)).toBeDefined();
        expect(spells.get(Spell_1.SpellName.illusoryDisguise)).toBeDefined();
    });
    it('should have charisma modifier for mana', () => {
        const modifiers = sheet.getSheetManaPoints().getFixedModifiers();
        const charismaModifier = modifiers.get(RoleAbilityName_1.RoleAbilityName.bardSpells);
        expect(charismaModifier).toBeDefined();
        expect(charismaModifier === null || charismaModifier === void 0 ? void 0 : charismaModifier.attributeBonuses).toEqual(['charisma']);
    });
});
