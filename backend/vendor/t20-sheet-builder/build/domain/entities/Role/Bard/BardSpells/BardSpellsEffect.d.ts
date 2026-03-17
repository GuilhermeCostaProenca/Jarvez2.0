import { Level, type Attributes } from '../../../Sheet';
import { SpellCircle, type LearnableSpellType, type Spell, type SpellSchool } from '../../../Spell';
import { type SpellLearnFrequency } from '../../SpellsAbility';
import { SpellsAbilityEffect } from '../../SpellsAbilityEffect';
export declare class BardSpellsEffect extends SpellsAbilityEffect {
    spellType: LearnableSpellType;
    spellsLearnFrequency: SpellLearnFrequency;
    spellsAttribute: keyof Attributes;
    circleLearnLevel: Record<SpellCircle, Level>;
    description: string;
    constructor(schools: Set<SpellSchool>, spells: Spell[]);
}
