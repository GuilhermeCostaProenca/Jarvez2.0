import type { ActivateableEffectParams, AffectableEffect, EffectRange, RangedEffect } from '../Ability/ActivateableAbilityEffect';
import { ActivateableAbilityEffect } from '../Ability/ActivateableAbilityEffect';
import type { Affectable } from '../Affectable/Affectable';
export type SpellEffectParams = ActivateableEffectParams;
export declare abstract class SpellEffect extends ActivateableAbilityEffect implements RangedEffect, AffectableEffect {
    abstract range: EffectRange;
    abstract affectable: Affectable;
}
