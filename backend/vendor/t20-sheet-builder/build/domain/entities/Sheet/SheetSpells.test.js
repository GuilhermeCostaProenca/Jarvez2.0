"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Spell_1 = require("../Spell");
const SheetSpells_1 = require("./SheetSpells");
describe('SheetSpells', () => {
    it('should have no learned circles', () => {
        const spells = new SheetSpells_1.SheetSpells();
        expect(spells.getLearnedCircles().arcane).toHaveLength(0);
        expect(spells.getLearnedCircles().divine).toHaveLength(0);
    });
    it('should have no learned schools', () => {
        const spells = new SheetSpells_1.SheetSpells();
        expect(spells.getLearnedSchools().arcane).toHaveLength(0);
        expect(spells.getLearnedSchools().divine).toHaveLength(0);
    });
    it('should learn spell circle with all its schools', () => {
        const spells = new SheetSpells_1.SheetSpells();
        spells.learnCircle(Spell_1.SpellCircle.first, 'arcane');
        expect(spells.getLearnedCircles().arcane).toContain(Spell_1.SpellCircle.first);
        expect(spells.getLearnedCircles().divine).toHaveLength(0);
        expect(spells.getLearnedSchools().arcane).toEqual(new Set([
            Spell_1.SpellSchool.abjuration,
            Spell_1.SpellSchool.divination,
            Spell_1.SpellSchool.enchantment,
            Spell_1.SpellSchool.evocation,
            Spell_1.SpellSchool.illusion,
            Spell_1.SpellSchool.necromancy,
            Spell_1.SpellSchool.summoning,
            Spell_1.SpellSchool.transmutation,
        ]));
        expect(spells.getLearnedSchools().divine).toEqual(new Set([]));
    });
    it('should learn spell from learned circle', () => {
        const spells = new SheetSpells_1.SheetSpells();
        spells.learnCircle(Spell_1.SpellCircle.first, 'arcane');
        spells.learnSpell(new Spell_1.ArcaneArmor());
        expect(spells.getSpells().get(Spell_1.SpellName.arcaneArmor)).toBeDefined();
    });
    it('should learn specific spell circle school', () => {
        const spells = new SheetSpells_1.SheetSpells();
        spells.learnCircle(Spell_1.SpellCircle.first, 'arcane', new Set([Spell_1.SpellSchool.abjuration]));
        expect(spells.getLearnedCircles().arcane).toContain(Spell_1.SpellCircle.first);
        expect(spells.getLearnedSchools().arcane).toEqual(new Set([
            Spell_1.SpellSchool.abjuration,
        ]));
    });
    it('should not learn spell from unlearned circle', () => {
        const spells = new SheetSpells_1.SheetSpells();
        expect(() => {
            spells.learnSpell(new Spell_1.ArcaneArmor());
        }).toThrowError();
    });
    it('should not learn spell from unlearned school', () => {
        const spells = new SheetSpells_1.SheetSpells();
        spells.learnCircle(Spell_1.SpellCircle.first, 'arcane', new Set([Spell_1.SpellSchool.abjuration]));
        expect(() => {
            spells.learnSpell(new Spell_1.MentalDagger());
        }).toThrowError('SCHOOL_NOT_LEARNED');
    });
});
