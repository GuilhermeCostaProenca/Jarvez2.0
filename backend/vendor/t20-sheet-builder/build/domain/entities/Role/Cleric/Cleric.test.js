"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const Spell_1 = require("../../Spell");
const CureWounds_1 = require("../../Spell/Divine/CureWounds");
const DivineProtection_1 = require("../../Spell/Divine/DivineProtection");
const FaithShield_1 = require("../../Spell/Divine/FaithShield");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Cleric_1 = require("./Cleric");
describe('Cleric', () => {
    let cleric;
    let sheet;
    let transaction;
    beforeEach(() => {
        cleric = new Cleric_1.Cleric([
            [Skill_1.SkillName.knowledge, Skill_1.SkillName.cure],
        ], [
            new FaithShield_1.FaithShield(),
            new DivineProtection_1.DivineProtection(),
            new CureWounds_1.CureWounds(),
        ]);
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        cleric.addToSheet(transaction);
    });
    it('should have faithful devote ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.clericFaithfulDevote)).toBeDefined();
    });
    it('should allow 2 granted powers as faithfull devote', () => {
        const devotion = sheet.getSheetDevotion();
        expect(devotion.getGrantedPowerCount()).toBe(2);
    });
    it('should have spells ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.clericSpells)).toBeDefined();
    });
    it('should be learn first level divine spells', () => {
        const spells = sheet.getSheetSpells();
        expect(spells.getLearnedCircles().divine).toContain(Spell_1.SpellCircle.first);
    });
    it('should learn initial spells', () => {
        const spells = sheet.getSheetSpells().getSpells();
        expect(spells.has(Spell_1.SpellName.faithShield)).toBe(true);
        expect(spells.has(Spell_1.SpellName.divineProtection)).toBe(true);
        expect(spells.has(Spell_1.SpellName.cureWounds)).toBe(true);
    });
    it('should have wisdom mana bonus', () => {
        const mana = sheet.getSheetManaPoints();
        const modifier = mana.getFixedModifiers().get(RoleAbilityName_1.RoleAbilityName.clericSpells);
        expect(modifier === null || modifier === void 0 ? void 0 : modifier.attributeBonuses).toContain('wisdom');
    });
});
