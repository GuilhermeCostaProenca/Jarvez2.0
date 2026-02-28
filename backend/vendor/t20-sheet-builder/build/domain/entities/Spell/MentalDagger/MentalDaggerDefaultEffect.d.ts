import type { EffectRange } from '../../Ability/ActivateableAbilityEffect';
import { EffectAffectableTarget } from '../../Ability/EffectAffectable';
import { ManaCost } from '../../ManaCost';
import { SpellEffect } from '../SpellEffect';
export declare class MentalDaggerDefaultEffect extends SpellEffect {
    description: string;
    baseCosts: ManaCost[];
    range: EffectRange;
    affectable: EffectAffectableTarget;
    constructor();
}
