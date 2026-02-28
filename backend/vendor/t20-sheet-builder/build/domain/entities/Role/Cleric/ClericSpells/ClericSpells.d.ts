import { AbilityEffects } from '../../../Ability';
import { type Spell } from '../../../Spell';
import { SpellsAbility } from '../../SpellsAbility';
import { ClericSpellsEffect } from './ClericSpellsEffect';
export declare class ClericSpells extends SpellsAbility {
    effects: AbilityEffects<{
        passive: {
            default: ClericSpellsEffect;
        };
    }>;
    constructor(spells: Spell[]);
}
