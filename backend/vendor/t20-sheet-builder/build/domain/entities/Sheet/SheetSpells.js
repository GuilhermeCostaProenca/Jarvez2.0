"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetSpells = void 0;
const errors_1 = require("../../errors");
const Spell_1 = require("../Spell");
class SheetSpells {
    constructor(spells = new Map(), learnedCircles = {
        arcane: new Set(),
        divine: new Set(),
    }, learnedSpellSchools = {
        arcane: new Set(),
        divine: new Set(),
    }) {
        this.spells = spells;
        this.learnedCircles = learnedCircles;
        this.learnedSpellSchools = learnedSpellSchools;
    }
    learnCircle(circle, type, schools = new Set([
        Spell_1.SpellSchool.abjuration,
        Spell_1.SpellSchool.divination,
        Spell_1.SpellSchool.enchantment,
        Spell_1.SpellSchool.evocation,
        Spell_1.SpellSchool.illusion,
        Spell_1.SpellSchool.necromancy,
        Spell_1.SpellSchool.summoning,
        Spell_1.SpellSchool.transmutation,
    ])) {
        this.learnedCircles[type].add(circle);
        schools.forEach(school => {
            this.learnedSpellSchools[type].add(school);
        });
    }
    learnSpell(spell, needsCircle = true, needsSchool = true) {
        if (needsCircle && !this.isSpellCircleLearned(spell)) {
            throw new errors_1.SheetBuilderError('CIRCLE_NOT_LEARNED');
        }
        if (needsSchool && !this.isSpellSchoolLearned(spell)) {
            throw new errors_1.SheetBuilderError('SCHOOL_NOT_LEARNED');
        }
        this.spells.set(spell.name, spell);
    }
    getLearnedCircles() {
        return this.learnedCircles;
    }
    getLearnedSchools() {
        return this.learnedSpellSchools;
    }
    getSpells() {
        return this.spells;
    }
    serializeLearnedCircles() {
        const circlesPerType = this.getLearnedCircles();
        const serialized = {
            arcane: [],
            divine: [],
        };
        Object.entries(circlesPerType).forEach(([type, circles]) => {
            serialized[type] = [...circles];
        });
        return serialized;
    }
    serializeSpells() {
        const serialized = [];
        this.getSpells().forEach(spell => {
            const serializedSpell = {
                name: spell.name,
                circle: spell.circle,
                abilityType: spell.abilityType,
                type: spell.type,
                effects: spell.effects.serialize(),
                school: spell.school,
                shortDescription: spell.shortDescription,
            };
            serialized.push(serializedSpell);
        });
        return serialized;
    }
    isSpellSchoolLearned(spell) {
        if (spell.type !== 'universal') {
            return this.learnedSpellSchools[spell.type].has(spell.school);
        }
        return this.learnedSpellSchools.arcane.has(spell.school) || this.learnedSpellSchools.divine.has(spell.school);
    }
    isSpellCircleLearned(spell) {
        if (spell.type !== 'universal') {
            return this.learnedCircles[spell.type].has(spell.circle);
        }
        return this.learnedCircles.arcane.has(spell.circle) || this.learnedCircles.divine.has(spell.circle);
    }
}
exports.SheetSpells = SheetSpells;
