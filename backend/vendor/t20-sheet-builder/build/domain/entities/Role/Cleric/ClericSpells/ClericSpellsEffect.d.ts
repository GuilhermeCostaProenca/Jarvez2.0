import { type Attributes, type Level } from '../../../Sheet';
import { SpellCircle, type LearnableSpellType, type Spell } from '../../../Spell';
import { type SpellLearnFrequency } from '../../SpellsAbility';
import { SpellsAbilityEffect } from '../../SpellsAbilityEffect';
export declare class ClericSpellsEffect extends SpellsAbilityEffect {
    spellType: LearnableSpellType;
    spellsLearnFrequency: SpellLearnFrequency;
    spellsAttribute: keyof Attributes;
    circleLearnLevel: Record<SpellCircle, Level>;
    description: string;
    constructor(spells: Spell[]);
}
