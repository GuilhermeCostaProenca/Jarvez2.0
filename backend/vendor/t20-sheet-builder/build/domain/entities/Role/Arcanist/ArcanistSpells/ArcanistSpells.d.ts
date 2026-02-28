import type { AbilityEffectsInterface } from '../../../Ability/AbilityEffects';
import type { Attribute } from '../../../Sheet/Attributes';
import type { Spell } from '../../../Spell/Spell';
import type { SpellLearnFrequency } from '../../SpellsAbility';
import { SpellsAbility } from '../../SpellsAbility';
import { ArcanistSpellsEffect } from './ArcanistSpellsEffect';
export declare class ArcanistSpells extends SpellsAbility {
    effects: AbilityEffectsInterface & {
        passive: {
            default: ArcanistSpellsEffect;
        };
    };
    constructor(spells: Spell[], learnFrequency: SpellLearnFrequency, attribute: Attribute);
}
