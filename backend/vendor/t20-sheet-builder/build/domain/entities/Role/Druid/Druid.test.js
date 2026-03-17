"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const Spell_1 = require("../../Spell");
const CureWounds_1 = require("../../Spell/Divine/CureWounds");
const DivineProtection_1 = require("../../Spell/Divine/DivineProtection");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Druid_1 = require("./Druid");
describe('Druid', () => {
    let sheet;
    let transaction;
    let druid;
    beforeEach(() => {
        druid = new Druid_1.Druid([
            [Skill_1.SkillName.animalHandling, Skill_1.SkillName.athletics, Skill_1.SkillName.animalRide, Skill_1.SkillName.knowledge],
        ], [new CureWounds_1.CureWounds(), new DivineProtection_1.DivineProtection()], new Set([Spell_1.SpellSchool.abjuration, Spell_1.SpellSchool.evocation, Spell_1.SpellSchool.divination]));
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        druid.addToSheet(transaction);
    });
    it('should have faithful devote ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.druidFaithfulDevote)).toBeDefined();
    });
    it('should allow 2 granted powers as faithfull devote', () => {
        const devotion = sheet.getSheetDevotion();
        expect(devotion.getGrantedPowerCount()).toBe(2);
    });
    it('should have wild empathy ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.wildEmpathy)).toBeDefined();
    });
    it('should have druid spells ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.druidSpells)).toBeDefined();
    });
    it('should learn first level divine spells on 3 schools', () => {
        const spells = sheet.getSheetSpells();
        expect(spells.getLearnedCircles().divine).toEqual(new Set([Spell_1.SpellCircle.first]));
        expect(spells.getLearnedSchools().divine).toEqual(new Set([Spell_1.SpellSchool.abjuration, Spell_1.SpellSchool.evocation, Spell_1.SpellSchool.divination]));
    });
    it('should have 2 spells on 1st circle', () => {
        const spells = sheet.getSheetSpells().getSpells();
        expect(spells.size).toBe(2);
    });
    it('should have wisdom modifier on mana', () => {
        const manaFixedModifiers = sheet.getSheetManaPoints().getFixedModifiers();
        expect(manaFixedModifiers.get(RoleAbilityName_1.RoleAbilityName.druidSpells)).toBeDefined();
    });
});
