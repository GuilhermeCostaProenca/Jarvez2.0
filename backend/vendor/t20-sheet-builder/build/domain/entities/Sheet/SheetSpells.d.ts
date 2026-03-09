import { type SpellCircle, type LearnableSpellType, type Spell, SpellSchool } from '../Spell';
import { type SerializedSheetSpell, type SerializedSheetLearnedCircles } from './SerializedSheet/SerializedSheetInterface';
import { type SheetLearnedSchools, type SheetLearnedCircles, type SheetSpellsInterface, type SpellMap } from './SheetSpellsInterface';
export declare class SheetSpells implements SheetSpellsInterface {
    private readonly spells;
    private readonly learnedCircles;
    private readonly learnedSpellSchools;
    constructor(spells?: SpellMap, learnedCircles?: SheetLearnedCircles, learnedSpellSchools?: SheetLearnedSchools);
    learnCircle(circle: SpellCircle, type: LearnableSpellType, schools?: Set<SpellSchool>): void;
    learnSpell(spell: Spell, needsCircle?: boolean, needsSchool?: boolean): void;
    getLearnedCircles(): SheetLearnedCircles;
    getLearnedSchools(): SheetLearnedSchools;
    getSpells(): SpellMap;
    serializeLearnedCircles(): SerializedSheetLearnedCircles;
    serializeSpells(): SerializedSheetSpell[];
    private isSpellSchoolLearned;
    private isSpellCircleLearned;
}
