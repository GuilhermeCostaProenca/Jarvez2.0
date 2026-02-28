import { AbilityEffects } from '../../../Ability';
import { type Spell, type SpellSchool } from '../../../Spell';
import { SpellsAbility } from '../../SpellsAbility';
import { DruidSpellsEffect } from './DruidSpellsEffect';
export declare class DruidSpells extends SpellsAbility {
    effects: AbilityEffects<{
        passive: {
            default: DruidSpellsEffect;
        };
    }>;
    constructor(spells: Spell[], schools: Set<SpellSchool>);
}
