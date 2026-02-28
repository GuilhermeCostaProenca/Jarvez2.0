import type { Attribute } from '../../../Sheet/Attributes';
import { Level } from '../../../Sheet/Level';
import type { LearnableSpellType, Spell } from '../../../Spell/Spell';
import { SpellCircle } from '../../../Spell/SpellCircle';
import type { SpellLearnFrequency } from '../../SpellsAbility';
import { SpellsAbilityEffect } from '../../SpellsAbilityEffect';
export declare class ArcanistSpellsEffect extends SpellsAbilityEffect {
    get description(): string;
    spellsLearnFrequency: SpellLearnFrequency;
    spellsAttribute: Attribute;
    circleLearnLevel: Record<SpellCircle, Level>;
    spellType: LearnableSpellType;
    constructor(spells: Spell[], learnFrequency: SpellLearnFrequency, attribute: Attribute);
}
